import json
import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from nexus.common.exceptions import BusinessError
from nexus.config.logger import get_logger

logger = get_logger(__name__)

_MODELS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "models.json")


class ModelConfig(BaseModel):
    model_name: Optional[str] = None
    model_id: str
    provider: Optional[str] = None
    api_key: str
    base_url: Optional[str] = None
    model_params: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    user_id: Optional[int] = None  # null = public, int = private (owner's uid)


def _load_models() -> list[dict]:
    with open(_MODELS_FILE, "r") as f:
        return json.load(f)


def fetch_model_config(model_config_id: int, auth_token: Optional[str] = None) -> Optional[ModelConfig]:
    """
    Fetch model config with ownership verification.
    - Public models: accessible by all
    - Private models: only accessible by owner
    """
    # Import here to avoid circular import
    from nexus.services.auth_service import extract_user

    models = _load_models()
    for m in models:
        if m.get("id") == model_config_id:
            if not m.get("enabled", True):
                raise BusinessError("当前模型配置已禁用，请切换其他模型")

            # Check ownership for private models
            m_user_id = m.get("user_id")
            if m_user_id is not None and m_user_id != 0:
                # Private model - verify ownership
                user = extract_user(auth_token)
                if not user or user.get("uid") != m_user_id:
                    raise BusinessError("无权访问该模型配置")

            model_id = str(m.get("model_id") or "").strip()
            if not model_id:
                raise BusinessError("模型配置缺少 model_id")
            return ModelConfig(
                model_name=m.get("model_name"),
                model_id=model_id,
                provider=m.get("provider"),
                api_key=m.get("api_key", ""),
                base_url=m.get("base_url"),
                model_params=m.get("model_params") if isinstance(m.get("model_params"), dict) else {},
                enabled=m.get("enabled", True),
                user_id=m.get("user_id"),
            )
    raise BusinessError(f"模型配置未找到: id={model_config_id}")


def list_model_configs(user_id: Optional[int] = None) -> list[dict]:
    """
    List models visible to a user.
    - If user_id is None: return only public models (user_id is null/0)
    - If user_id is provided: return public + user's private models
    """
    models = _load_models()
    result = []
    for m in models:
        m_user_id = m.get("user_id")
        # Public model (user_id is null or 0) - visible to all
        if m_user_id is None or m_user_id == 0:
            result.append(m)
        # Private model owned by this user
        elif user_id and m_user_id == user_id:
            result.append(m)
    return result
