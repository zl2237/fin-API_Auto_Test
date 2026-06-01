import os
from loguru import logger
from config.settings import LOG_DIR
from datetime import datetime

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, f"auto_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logger.add(
    log_file,
    rotation="500MB",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

log = logger