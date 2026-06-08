"""API 兼容路由 — 替代原 Spring Boot API 服务"""
import json
import os
import re
import time
import uuid
from base64 import b64decode

import bcrypt
import jwt
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from fastapi import APIRouter, Request
from pydantic import BaseModel, field_validator

from nexus.common.exceptions import AuthError
from nexus.config.logger import get_logger
from nexus.core.cache import CacheManager

logger = get_logger(__name__)

router = APIRouter(prefix="/fastflow/api/v1", tags=["api-compat"])

JWT_SECRET = "fastflow-local-dev-jwt-secret-key-2026"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 604800  # 7 days
AES_KEY = b"d7b8a2c9e4f10536"

_USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "config", "users.json")
_MODELS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "config", "models.json")
_INVITE_CODES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "config", "invite_codes.json")


def _load_users() -> list[dict]:
    if os.path.exists(_USERS_FILE):
        with open(_USERS_FILE, "r") as f:
            return json.load(f)
    return []


def _save_users(users: list[dict]) -> None:
    with open(_USERS_FILE, "w") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def _load_models() -> list[dict]:
    if os.path.exists(_MODELS_FILE):
        with open(_MODELS_FILE, "r") as f:
            return json.load(f)
    return []


def _save_models(models: list[dict]) -> None:
    with open(_MODELS_FILE, "w") as f:
        json.dump(models, f, indent=2, ensure_ascii=False)


def _load_invite_codes() -> list[dict]:
    if os.path.exists(_INVITE_CODES_FILE):
        with open(_INVITE_CODES_FILE, "r") as f:
            return json.load(f)
    return []


def _save_invite_codes(codes: list[dict]) -> None:
    with open(_INVITE_CODES_FILE, "w") as f:
        json.dump(codes, f, indent=2, ensure_ascii=False)


def _decrypt_password(encrypted: str) -> str:
    if not encrypted:
        return encrypted
    try:
        cipher = AES.new(AES_KEY, AES.MODE_ECB)
        raw = b64decode(encrypted)
        return unpad(cipher.decrypt(raw), 16).decode("utf-8")
    except Exception:
        return encrypted


def _generate_jwt(uid: int, email: str) -> str:
    payload = {
        "uid": uid,
        "email": email,
        "expire_time": int(time.time() * 1000) + JWT_EXPIRATION * 1000,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _make_response(code: int, message: str, data=None):
    return {"code": code, "message": message, "data": data}


# === Auth endpoints ===

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    inviteCode: str


# Well-known provider default base URLs. LiteLLM uses these natively
# when custom_llm_provider matches; user-supplied base_url overrides them.
_PROVIDER_DEFAULT_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "deepseek": "https://api.deepseek.com/v1",
    "minimax": "https://api.minimaxi.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "glm": "https://open.bigmodel.cn/api/paas/v4",
    "moonshot": "https://api.moonshot.cn/v1",
}

# Patterns that indicate an API key was accidentally pasted into the base_url field
_API_KEY_PATTERNS = [
    re.compile(r"^sk-", re.IGNORECASE),      # common API key prefix
    re.compile(r"^Bearer\s", re.IGNORECASE),  # Bearer token
    re.compile(r"^[A-Za-z0-9+/]{40,}$"),     # bare token (long base64-like string)
]


class CreateModelRequest(BaseModel):
    model_name: str
    model_id: str
    provider: str
    api_key: str
    base_url: str = ""
    model_params: dict = {}

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str, info) -> str:
        """Validate that base_url is a proper URL, not an API key."""
        v = (v or "").strip()
        if not v:
            return v
        for pattern in _API_KEY_PATTERNS:
            if pattern.match(v):
                provider = info.data.get("provider", "") if info.data else ""
                default = _PROVIDER_DEFAULT_BASE_URLS.get(provider, "")
                raise ValueError(
                    f"base_url appears to be an API key (starts with 'sk-' or looks like a token). "
                    f"Please enter a proper URL. "
                    + (f"For {provider}, the default is: {default}" if default else "")
                )
        if not re.match(r"^https?://", v):
            raise ValueError("base_url must start with http:// or https://")
        return v


@router.post("/auth/login")
async def login(req: LoginRequest):
    real_password = _decrypt_password(req.password)
    if len(real_password) < 6:
        return _make_response(400, "密码错误")

    users = _load_users()
    for u in users:
        if u.get("email") == req.email and u.get("status") == 1:
            stored = u.get("password", "")
            if stored and bcrypt.checkpw(real_password.encode(), stored.encode()):
                token = _generate_jwt(u["uid"], u["email"])
                return _make_response(200, "Success", {
                    "token": token,
                    "userInfo": {
                        "uid": u["uid"],
                        "username": u["username"],
                        "email": u["email"],
                        "status": u.get("status", 1),
                        "createdAt": u.get("created_at", ""),
                        "updatedAt": u.get("updated_at", ""),
                    }
                })
    return _make_response(400, "邮箱或密码错误")


@router.post("/auth/register")
async def register(req: RegisterRequest):
    real_password = _decrypt_password(req.password)
    if len(real_password) < 6:
        return _make_response(400, "密码长度不能少于6位")

    # 验证邀请码
    invite_code = (req.inviteCode or "").strip().upper()
    if not invite_code:
        return _make_response(400, "邀请码不能为空", {"fieldErrors": {"inviteCode": "邀请码不能为空"}})
    if len(invite_code) != 6 or not re.match(r"^[A-Z0-9]+$", invite_code):
        return _make_response(400, "邀请码格式不正确", {"fieldErrors": {"inviteCode": "邀请码必须是6位字母或数字"}})

    invite_codes = _load_invite_codes()
    found = None
    for c in invite_codes:
        if c.get("code") == invite_code:
            found = c
            break
    if not found:
        return _make_response(400, "邀请码无效", {"fieldErrors": {"inviteCode": "邀请码无效"}})
    if found.get("used"):
        return _make_response(400, "邀请码已被使用", {"fieldErrors": {"inviteCode": "邀请码已被使用"}})

    users = _load_users()
    for u in users:
        if u.get("email") == req.email:
            return _make_response(400, "该邮箱已被注册", {"fieldErrors": {"email": "该邮箱已被注册"}})

    hashed = bcrypt.hashpw(real_password.encode(), bcrypt.gensalt()).decode()
    import random
    uid = random.randint(100000000, 999999999)
    new_user = {
        "uid": uid,
        "username": req.username,
        "email": req.email,
        "password": hashed,
        "status": 1,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    users.append(new_user)
    _save_users(users)

    # 标记邀请码已使用
    found["used"] = True
    found["used_by"] = req.email
    found["used_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save_invite_codes(invite_codes)

    logger.info("User registered: uid=%s email=%s invite=%s", uid, req.email, invite_code)
    return _make_response(200, "Success", {"uid": uid, "username": req.username, "email": req.email})


@router.post("/auth/checkLogin")
async def check_login(request: Request):
    auth_token = request.headers.get("Authorization", "")
    if auth_token.startswith("Bearer "):
        auth_token = auth_token[7:]

    try:
        payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        expire_time = payload.get("expire_time")
        if expire_time and time.time() * 1000 > expire_time:
            return _make_response(401, "未登录或登录已过期")
        uid = payload.get("uid")
        email = payload.get("email")
        users = _load_users()
        for u in users:
            if u.get("uid") == uid and u.get("email") == email:
                return _make_response(200, "Success", {
                    "uid": uid, "username": u.get("username"), "email": email
                })
        return _make_response(401, "用户不存在")
    except Exception:
        return _make_response(401, "未登录或登录已过期")


@router.post("/auth/refresh")
async def refresh_token(request: Request):
    auth_token = request.headers.get("Authorization", "")
    if auth_token.startswith("Bearer "):
        auth_token = auth_token[7:]

    try:
        payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        uid = payload.get("uid")
        email = payload.get("email")
        
        users = _load_users()
        for u in users:
            if u.get("uid") == uid and u.get("email") == email:
                new_token = _generate_jwt(uid, email)
                return _make_response(200, "Success", {
                    "token": new_token,
                    "userInfo": {
                        "uid": uid,
                        "username": u.get("username"),
                        "email": email,
                        "status": u.get("status", 1),
                        "createdAt": u.get("created_at", ""),
                        "updatedAt": u.get("updated_at", ""),
                    }
                })
        return _make_response(401, "用户不存在")
    except jwt.ExpiredSignatureError:
        return _make_response(401, "Token已过期，请重新登录")
    except Exception:
        return _make_response(401, "Token无效")


# === Model Config endpoints ===

@router.get("/model_config/list")
async def list_models(request: Request):
    # Extract user from JWT token
    auth_token = request.headers.get("Authorization")
    user_id = None
    if auth_token:
        try:
            from nexus.services.auth_service import extract_user
            user = extract_user(auth_token)
            if user:
                user_id = user.get("uid")
        except Exception:
            pass  # Ignore auth errors for list endpoint

    models = _load_models()
    result = []
    for m in models:
        m_user_id = m.get("user_id")
        # Public model (user_id is null or 0) - visible to all
        if m_user_id is None or m_user_id == 0:
            result.append({
                "id": m["id"],
                "modelName": m["model_name"],
                "modelId": m["model_id"],
                "provider": m.get("provider"),
                "enabled": m.get("enabled", True),
                "baseUrl": m.get("base_url"),
                "sortOrder": m.get("sort_order", 0),
                "userId": m.get("user_id"),
            })
        # Private model owned by this user
        elif user_id and m_user_id == user_id:
            result.append({
                "id": m["id"],
                "modelName": m["model_name"],
                "modelId": m["model_id"],
                "provider": m.get("provider"),
                "enabled": m.get("enabled", True),
                "baseUrl": m.get("base_url"),
                "sortOrder": m.get("sort_order", 0),
                "userId": m.get("user_id"),
            })
    return _make_response(200, "Success", result)


@router.get("/model_config/{model_id}")
async def get_model(model_id: int):
    models = _load_models()
    for m in models:
        if m["id"] == model_id:
            return _make_response(200, "Success", {
                "id": m["id"],
                "modelName": m["model_name"],
                "modelId": m["model_id"],
                "provider": m.get("provider"),
                "apiKey": m.get("api_key"),
                "baseUrl": m.get("base_url"),
                "modelParamsJson": json.dumps(m.get("model_params", {})),
                "enabled": m.get("enabled", True),
                "sortOrder": m.get("sort_order", 0),
            })
    return _make_response(404, "模型配置未找到")


@router.post("/model_config")
async def create_model(req: CreateModelRequest, request: Request):
    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return _make_response(401, "未登录")

    from nexus.services.auth_service import extract_user
    user = extract_user(auth_token)
    if not user:
        return _make_response(401, "未登录")

    user_id = user.get("uid")
    models = _load_models()

    private_count = sum(1 for m in models if m.get("user_id") == user_id)
    if private_count >= 2:
        return _make_response(400, "每个用户最多添加2个私有模型")

    new_id = max(m["id"] for m in models) + 1 if models else 10001

    new_model = {
        "id": new_id,
        "model_name": req.model_name,
        "model_id": req.model_id,
        "provider": req.provider,
        "api_key": req.api_key,
        "base_url": req.base_url,
        "model_params": req.model_params,
        "enabled": True,
        "user_id": user_id,
    }
    models.append(new_model)
    _save_models(models)
    CacheManager.clear_all_llm_runtimes()

    logger.info("User %s created private model: id=%s name=%s", user_id, new_id, req.model_name)
    return _make_response(200, "Success", {"id": new_id})


@router.put("/model_config/{model_id}")
async def update_model(model_id: int, req: CreateModelRequest, request: Request):
    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return _make_response(401, "未登录")

    from nexus.services.auth_service import extract_user
    user = extract_user(auth_token)
    if not user:
        return _make_response(401, "未登录")

    user_id = user.get("uid")
    models = _load_models()

    for m in models:
        if m["id"] == model_id:
            m_user_id = m.get("user_id")

            if m_user_id is None or m_user_id == 0:
                return _make_response(403, "无法修改公共模型")
            if m_user_id != user_id:
                return _make_response(403, "无权修改该模型")

            m["model_name"] = req.model_name
            m["model_id"] = req.model_id
            m["provider"] = req.provider
            m["api_key"] = req.api_key
            m["base_url"] = req.base_url
            m["model_params"] = req.model_params
            m["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

            _save_models(models)
            CacheManager.clear_all_llm_runtimes()
            logger.info("User %s updated private model: id=%s", user_id, model_id)
            return _make_response(200, "Success")

    return _make_response(404, "模型配置未找到")


@router.delete("/model_config/{model_id}")
async def delete_model(model_id: int, request: Request):
    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return _make_response(401, "未登录")

    from nexus.services.auth_service import extract_user
    user = extract_user(auth_token)
    if not user:
        return _make_response(401, "未登录")

    user_id = user.get("uid")
    models = _load_models()

    for i, m in enumerate(models):
        if m["id"] == model_id:
            m_user_id = m.get("user_id")

            if m_user_id is None or m_user_id == 0:
                return _make_response(403, "无法删除公共模型")
            if m_user_id != user_id:
                return _make_response(403, "无权删除该模型")

            models.pop(i)
            _save_models(models)
            CacheManager.clear_all_llm_runtimes()
            logger.info("User %s deleted private model: id=%s", user_id, model_id)
            return _make_response(200, "Success")

    return _make_response(404, "模型配置未找到")


# === Slash catalog (pass-through to Nexus slash endpoint) ===

@router.get("/clash/catalog")
async def clash_catalog():
    return _make_response(200, "Success", [])
