from flask import Blueprint, jsonify, request, current_app

from services.store import store
from services.test_runner import run_test

bp = Blueprint("run", __name__)


@bp.route("/api/run", methods=["POST"])
def start_run():
    try:
        data = request.get_json(silent=True) or {}
        marker = (data.get("marker") or "").strip()
        if not marker:
            return jsonify({"ok": False, "message": "marker 不能为空"}), 400

        required_env = ["base_url", "login_url", "test_username", "test_password"]
        missing = [k for k in required_env if not (data.get(k) or "").strip()]
        if missing:
            return jsonify({"ok": False, "message": f"缺少必填项: {', '.join(missing)}"}), 400

        current_app.logger.info(f"Starting test run: marker={marker}, base_url={data.get('base_url')}")
        record = store.create(marker, data)
        run_test(record.run_id, marker, data)
        current_app.logger.info(f"Test run created: run_id={record.run_id}")
        return jsonify({"ok": True, "run_id": record.run_id, "marker": marker})
    except Exception as e:
        current_app.logger.exception(f"Error in start_run: {e}")
        return jsonify({"ok": False, "message": f"启动测试失败: {str(e)}"}), 500


@bp.route("/api/run/<run_id>", methods=["GET"])
def get_run(run_id: str):
    try:
        record = store.get(run_id)
        if not record:
            return jsonify({"ok": False, "message": "run_id 不存在"}), 404
        return jsonify({
            "ok": True,
            "run_id": record.run_id,
            "marker": record.marker,
            "status": record.status,
            "started_at": record.started_at,
            "finished_at": record.finished_at,
            "result": record.result,
            "logs": record.logs,
        })
    except Exception as e:
        current_app.logger.exception(f"Error in get_run({run_id}): {e}")
        return jsonify({"ok": False, "message": f"获取运行状态失败: {str(e)}"}), 500
