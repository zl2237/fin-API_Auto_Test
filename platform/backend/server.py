import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from loguru import logger

from api.auth import bp as auth_bp
from api.markers import bp as markers_bp
from api.run import bp as run_bp
from api.logs import bp as logs_bp
from api.users import bp as users_bp

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH, override=True)


def setup_logging():
    """配置 loguru 日志"""
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 添加文件输出
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "app.log",
        rotation="00:00",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=False,
    )
    
    # 拦截 Flask 的标准 logging，让 app.logger 也通过 loguru 输出
    class LoguruHandler(logging.Handler):
        def emit(self, record):
            level = record.levelname
            message = record.getMessage()
            if record.exc_info:
                logger.opt(exception=record.exc_info).error(message)
            else:
                logger.log(level, message)
    
    handler = LoguruHandler()
    handler.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    for logger_name in ['werkzeug', 'flask']:
        lg = logging.getLogger(logger_name)
        lg.addHandler(handler)
        lg.setLevel(logging.INFO)
        lg.propagate = False


def create_app():
    setup_logging()
    
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-prod")
    CORS(app, supports_credentials=True)

    # 配置请求日志
    @app.before_request
    def log_request_info():
        app.logger.info(f"[{request.method}] {request.path} - {request.remote_addr}")

    @app.after_request
    def log_response_info(response):
        app.logger.info(f"[{request.method}] {request.path} -> {response.status_code}")
        return response

    # 全局异常处理器
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.exception(f"Unhandled exception: {e}")
        return jsonify({"ok": False, "message": f"服务器内部错误: {str(e)}"}), 500

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"ok": False, "message": "资源不存在"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"ok": False, "message": "方法不允许"}), 405

    app.register_blueprint(auth_bp)
    app.register_blueprint(markers_bp)
    app.register_blueprint(run_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(users_bp)

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        dist_dir = Path(__file__).resolve().parent / "static" / "dist"
        if path and (dist_dir / path).exists():
            return send_from_directory(str(dist_dir), path)
        return send_from_directory(str(dist_dir), "index.html")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PLATFORM_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    logger.info(f"[Platform] Backend starting on http://127.0.0.1:{port} (debug={debug})")
    app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=False)
