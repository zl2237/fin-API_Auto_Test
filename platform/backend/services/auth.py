import os
import secrets
from typing import Optional

PLATFORM_USERS = {
    os.getenv("PLATFORM_USER", "admin"): os.getenv("PLATFORM_PASSWORD", "admin123"),
}


def validate(username: str, password: str) -> tuple[bool, Optional[str]]:
    expected = PLATFORM_USERS.get(username)
    if expected is None:
        return False, "账号不存在"
    if expected != password:
        return False, "密码错误"
    return True, None


def make_token(username: str) -> str:
    return f"{username}.{secrets.token_hex(16)}"
