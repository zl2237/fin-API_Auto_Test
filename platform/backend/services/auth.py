import os
import secrets
from typing import Optional

from services.db import db


def get_user(username: str) -> Optional[dict]:
    with db._cursor() as cursor:
        cursor.execute("SELECT username, password, role FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return None
        return {"username": row["username"], "password": row["password"], "role": row["role"]}


def validate(username: str, password: str) -> tuple[bool, Optional[str]]:
    user = get_user(username)
    if not user:
        return False, "账号不存在"
    if user["password"] != password:
        return False, "密码错误"
    return True, None


def get_role(username: str) -> str:
    user = get_user(username)
    if not user:
        return "user"
    return user["role"]


def make_token(username: str) -> str:
    role = get_role(username)
    payload = f"{username}:{role}.{secrets.token_hex(16)}"
    return payload
