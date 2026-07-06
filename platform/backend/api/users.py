from typing import Optional

from flask import Blueprint, jsonify, request

from services.auth import get_role
from services.users import user_service

bp = Blueprint("users", __name__)


def _require_admin() -> Optional[dict]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None
    try:
        token_part = auth_header.split(".", 1)[0]
        username = token_part.split(":", 1)[0]
        role = get_role(username)
    except Exception:
        return None
    if role != "admin":
        return None
    return {"username": username, "role": role}


@bp.route("/api/users", methods=["GET"])
def list_users():
    operator = _require_admin()
    if not operator:
        return jsonify({"ok": False, "message": "无权限"}), 403
    users = user_service.list()
    return jsonify({"ok": True, "users": users})


@bp.route("/api/users", methods=["POST"])
def create_user():
    operator = _require_admin()
    if not operator:
        return jsonify({"ok": False, "message": "无权限"}), 403
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "user").strip()
    if not username or not password:
        return jsonify({"ok": False, "message": "账号和密码不能为空"}), 400
    if role not in {"admin", "user"}:
        return jsonify({"ok": False, "message": "角色无效"}), 400
    try:
        user_service.create(username, password, role)
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    return jsonify({"ok": True})


@bp.route("/api/users/<username>", methods=["PUT"])
def update_user(username: str):
    operator = _require_admin()
    if not operator:
        return jsonify({"ok": False, "message": "无权限"}), 403
    if operator["username"] == username:
        return jsonify({"ok": False, "message": "不支持修改当前账号"}), 400
    data = request.get_json(silent=True) or {}
    password = data.get("password")
    role = data.get("role")
    if role is not None and role not in {"admin", "user"}:
        return jsonify({"ok": False, "message": "角色无效"}), 400
    try:
        user_service.update(username, password, role)
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    return jsonify({"ok": True})


@bp.route("/api/users/<username>", methods=["DELETE"])
def delete_user(username: str):
    operator = _require_admin()
    if not operator:
        return jsonify({"ok": False, "message": "无权限"}), 403
    if operator["username"] == username:
        return jsonify({"ok": False, "message": "不支持删除当前账号"}), 400
    try:
        user_service.delete(username)
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    return jsonify({"ok": True})
