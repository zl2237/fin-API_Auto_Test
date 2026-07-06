from __future__ import annotations

from typing import List, Optional

from services.db import db


class UserService:
    def list(self) -> List[dict]:
        with db._cursor() as cursor:
            cursor.execute("SELECT username, role, created_at, updated_at FROM users ORDER BY username")
            rows = cursor.fetchall()
            return [
                {
                    "username": row["username"],
                    "role": row["role"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ]

    def get(self, username: str) -> Optional[dict]:
        with db._cursor() as cursor:
            cursor.execute("SELECT username, role, created_at, updated_at FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "username": row["username"],
                "role": row["role"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def create(self, username: str, password: str, role: str) -> dict:
        with db._cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role),
            )
        return {"username": username, "role": role}

    def update(self, username: str, password: Optional[str], role: Optional[str]) -> dict:
        fields = []
        values = []
        if password is not None:
            fields.append("password = ?")
            values.append(password)
        if role is not None:
            fields.append("role = ?")
            values.append(role)
        if not fields:
            return {"username": username, "role": self.get(username)["role"]}
        values.append(username)
        with db._cursor() as cursor:
            cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE username = ?", values)
        return {"username": username, "role": role if role is not None else self.get(username)["role"]}

    def delete(self, username: str) -> None:
        with db._cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))


user_service = UserService()
