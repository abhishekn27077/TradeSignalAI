import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import get_settings


# Regular expressions for sensitive credentials
SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(?:authorization:\s*bearer\s+)[^\s"\',]+'), 'Authorization: Bearer [REDACTED]'),
    (re.compile(r'(?i)(?:bearer\s+)[a-zA-Z0-9_\-\.]{15,}'), 'Bearer [REDACTED]'),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'AIza[0-9A-Za-z-_]{35}'), '[REDACTED_API_KEY]'),
    (re.compile(r'nvapi-[a-zA-Z0-9_\-]{25,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'sk-or-v1-[a-zA-Z0-9]{35,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'(?i)(postgres|postgresql|mysql|mongodb|redis):\/\/[^:\s]+:[^@\s]+@'), r'\1://[REDACTED_DB_CREDENTIALS]@'),
    (re.compile(r'(?i)(?:password|passwd|secret_key|client_secret)\s*[:=]\s*["\']?[^\s"\',&]{4,}["\']?'), 'password=[REDACTED]'),
    (re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'), '[REDACTED_PRIVATE_KEY]'),
]


def redact_sensitive_text(text: str) -> str:
    """Safely redact credentials, tokens, passwords, and connection strings from text."""
    if not isinstance(text, str):
        return text
    for pat, repl in SENSITIVE_PATTERNS:
        text = pat.sub(repl, text)
    return text


class SecretRedactionFilter(logging.Filter):
    """Logging filter that redacts credentials from log records before dispatch."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_text(record.msg)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(redact_sensitive_text(str(a)) if isinstance(a, str) else a for a in record.args)
            elif isinstance(record.args, dict):
                record.args = {k: redact_sensitive_text(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
        return True


class JSONFormatter(logging.Formatter):
    """
    Format logs as JSON for structured logging with credential redaction.
    """
    def format(self, record: logging.LogRecord) -> str:
        msg = redact_sensitive_text(record.getMessage())
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "message": msg,
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }
        
        # Include exception info if present, with redaction
        if record.exc_info:
            raw_exc = self.formatException(record.exc_info)
            log_obj["exception"] = redact_sensitive_text(raw_exc)
            
        # Include correlation_id if injected via log record (e.g. from middleware)
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id

        return json.dumps(log_obj)


def setup_logging():
    """
    Configure application logging with automatic credential redaction.
    Sets up both Console (human-readable) and File (JSON structured) handlers.
    """
    settings = get_settings()
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()

    redaction_filter = SecretRedactionFilter()
    root_logger.addFilter(redaction_filter)

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.addFilter(redaction_filter)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    console_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    from logging.handlers import RotatingFileHandler
    
    # 2. File Handler (JSON)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 10 MB per file, keep 5 backups
    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.addFilter(redaction_filter)
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
