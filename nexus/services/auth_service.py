import json
import os
import time
from typing import Optional

import jwt

from nexus.config.logger import get_logger

logger = get_logger(__name__)

JWT_SECRET = "fastflow-local-dev-jwt-secret-key-2026"
JWT_ALGORITHM = "HS256"
_USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "users.json")


def _load_users() -> list[dict]:
    with open(_USERS_FILE, "r") as f:
        return json.load(f)


def check_login(auth_token: Optional[str] = None) -> bool:
    if not auth_token:
        logger.warning("Check login without Authorization, skip.")
        return False

    if auth_token.startswith("Bearer "):
        auth_token = auth_token[7:]

    try:
        payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        expire_time = payload.get("expire_time")
        if expire_time and time.time() * 1000 > expire_time:
            logger.warning("JWT token expired")
            return False

        uid = payload.get("uid")
        email = payload.get("email")
        if not uid or not email:
            logger.warning("JWT token missing uid or email")
            return False

        users = _load_users()
        for u in users:
            if u.get("uid") == uid and u.get("email") == email and u.get("status") == 1:
                return True

        logger.warning("User not found or disabled: uid=%s email=%s", uid, email)
        return False

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return False
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid JWT token: %s", e)
        return False
    except Exception as e:
        logger.error("Error checking login: %s", e)
        return False


def extract_user(auth_token: Optional[str] = None) -> Optional[dict]:
    """
    Extract user info from JWT token.
    Returns dict with uid, username, email or None if invalid.
    """
    if not auth_token:
        return None

    if auth_token.startswith("Bearer "):
        auth_token = auth_token[7:]

    try:
        payload = jwt.decode(auth_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        expire_time = payload.get("expire_time")
        if expire_time and time.time() * 1000 > expire_time:
            return None

        uid = payload.get("uid")
        email = payload.get("email")
        if not uid or not email:
            return None

        users = _load_users()
        for u in users:
            if u.get("uid") == uid and u.get("email") == email and u.get("status") == 1:
                return {
                    "uid": u["uid"],
                    "username": u.get("username"),
                    "email": u["email"],
                }

        return None

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        logger.error("Error extracting user: %s", e)
        return None
