from flask import Blueprint, Response, stream_with_context, jsonify, current_app

from services.store import store

bp = Blueprint("logs", __name__)


@bp.route("/api/run/<run_id>/logs", methods=["GET"])
def stream_logs(run_id: str):
    try:
        record = store.get(run_id)
        if not record:
            return Response("run_id 不存在", status=404)

        def event_stream():
            sent = 0
            while True:
                rec = store.get(run_id)
                if not rec:
                    break
                logs = rec.logs
                while sent < len(logs):
                    yield f"data: {logs[sent]}\n\n"
                    sent += 1
                if rec.status in ("completed", "failed"):
                    yield "event: done\ndata: \n\n"
                    break

        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
        return Response(stream_with_context(event_stream()), mimetype="text/event-stream", headers=headers)
    except Exception as e:
        current_app.logger.exception(f"Error in stream_logs({run_id}): {e}")
        return jsonify({"ok": False, "message": f"获取日志流失败: {str(e)}"}), 500
