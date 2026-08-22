import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import get_settings


class JSONFormatter(logging.Formatter):
    """
    Format logs as JSON for structured logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }
        
        # Include exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        # Include correlation_id if injected via log record (e.g. from middleware)
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id

        return json.dumps(log_obj)

def setup_logging():
    """
    Configure application logging.
    Sets up both Console (human-readable) and File (JSON structured) handlers.
    """
    settings = get_settings()
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    console_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    from logging.handlers import RotatingFileHandler
    
    # 2. File Handler (JSON)
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 10 MB per file, keep 5 backups
    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Reduce uvicorn spam
    
    # Suppress extremely noisy third-party libraries
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("peewee").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("data").setLevel(logging.WARNING)
    logging.getLogger("utils").setLevel(logging.WARNING)
    logging.getLogger("history").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
