from flask import Blueprint, jsonify, request

from services.auth import validate, make_token, get_role

bp = Blueprint("auth", __name__)


@bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    ok, error = validate(username, password)
    if not ok:
        return jsonify({"ok": False, "message": error}), 401
    token = make_token(username)
    role = get_role(username)
    return jsonify({"ok": True, "token": token, "username": username, "role": role})
