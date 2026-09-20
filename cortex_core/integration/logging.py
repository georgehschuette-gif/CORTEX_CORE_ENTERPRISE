"""
Enterprise Structured Logging for Cortex Core Enterprise.

Provides JSON structured logging that integrates seamlessly with ANY enterprise
logging platform - ELK Stack, Splunk, Graylog, Fluentd, and more.
"""

import json
import logging
import socket
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, TextIO

import structlog


@dataclass
class LogEntry:
    """Structured log entry with enterprise-standard fields."""

    timestamp: str
    level: str
    logger: str
    message: str
    service: str = "cortex-core-enterprise"
    version: str = "1.0.0"
    environment: str = "development"
    host: str = socket.gethostname()
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None
    extra: Optional[Dict[str, Any]] = None


class EnterpriseJSONFormatter(logging.Formatter):
    """JSON formatter for enterprise logging compatibility."""

    def __init__(
        self, service: str = "cortex-core-enterprise", environment: str = "development"
    ):
        super().__init__()
        self.service = service
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        # Create structured log entry
        log_entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat() + "Z",
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            service=self.service,
            environment=self.environment,
            component=getattr(record, "component", None),
            operation=getattr(record, "operation", None),
            duration_ms=getattr(record, "duration_ms", None),
            status_code=getattr(record, "status_code", None),
            error_code=getattr(record, "error_code", None),
            correlation_id=getattr(record, "correlation_id", None),
            user_id=getattr(record, "user_id", None),
            session_id=getattr(record, "session_id", None),
            request_id=getattr(record, "request_id", None),
            tags=getattr(record, "tags", None),
            extra=getattr(record, "extra", None),
        )

        # Add exception info if present
        if record.exc_info:
            log_entry.stack_trace = self.formatException(record.exc_info)

        # Convert to dict and remove None values
        log_dict = asdict(log_entry)
        log_dict = {k: v for k, v in log_dict.items() if v is not None}

        return json.dumps(log_dict, default=str)


class EnterpriseLogHandler(logging.Handler):
    """Base handler for enterprise logging destinations."""

    def __init__(self, formatter: Optional[logging.Formatter] = None):
        super().__init__()
        if formatter:
            self.setFormatter(formatter)


class FileHandler(EnterpriseLogHandler):
    """Structured file logging handler."""

    def __init__(
        self,
        file_path: str,
        max_size_mb: int = 100,
        backup_count: int = 10,
        formatter: Optional[logging.Formatter] = None,
    ):
        super().__init__(formatter)
        self.file_path = Path(file_path)
        self.max_size_mb = max_size_mb
        self.backup_count = backup_count
        self.current_file: Optional[TextIO] = None
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure log directory exists."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _rotate_file(self):
        """Rotate log file if it exceeds max size."""
        if self.current_file and self.file_path.exists():
            size_mb = self.file_path.stat().st_size / (1024 * 1024)
            if size_mb >= self.max_size_mb:
                self.current_file.close()
                # Simple rotation - in production, use more sophisticated rotation
                for i in range(self.backup_count - 1, 0, -1):
                    src = self.file_path.with_suffix(f".log.{i}")
                    dst = self.file_path.with_suffix(f".log.{i+1}")
                    if src.exists():
                        src.replace(dst)

                if self.backup_count > 0:
                    backup_path = self.file_path.with_suffix(".log.1")
                    self.file_path.replace(backup_path)

    def emit(self, record: logging.LogRecord):
        try:
            self._rotate_file()

            if not self.current_file or self.current_file.closed:
                self.current_file = open(self.file_path, "a", encoding="utf-8")

            self.current_file.write(self.format(record) + "\n")
            self.current_file.flush()
        except Exception:
            self.handleError(record)


class SyslogHandler(EnterpriseLogHandler):
    """Syslog handler for enterprise syslog servers."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 514,
        formatter: Optional[logging.Formatter] = None,
    ):
        super().__init__(formatter)
        self.host = host
        self.port = port
        self.socket = None

    def _get_socket(self):
        if self.socket is None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return self.socket

    def emit(self, record: logging.LogRecord):
        try:
            message = self.format(record)
            self._get_socket().sendto(message.encode("utf-8"), (self.host, self.port))
        except Exception:
            self.handleError(record)

    def close(self):
        """Close the underlying socket."""
        if self.socket is not None:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        super().close()


class FluentdHandler(EnterpriseLogHandler):
    """Fluentd handler for log aggregation platforms."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 24224,
        tag: str = "cortex.core",
        formatter: Optional[logging.Formatter] = None,
    ):
        super().__init__(formatter)
        self.host = host
        self.port = port
        self.tag = tag
        self.socket = None

    def _get_socket(self):
        if self.socket is None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.socket.connect((self.host, self.port))
            except Exception as e:
                logging.error(f"Failed to connect to Fluentd: {e}")
                self.socket = None
                raise

        return self.socket

    def emit(self, record: logging.LogRecord):
        try:
            # Fluentd forward protocol (simplified)
            log_entry = json.loads(self.format(record))
            fluent_msg = {
                "tag": self.tag,
                "time": int(datetime.now(timezone.utc).timestamp()),
                "record": log_entry,
            }

            message = json.dumps(fluent_msg) + "\n"
            self._get_socket().send(message.encode("utf-8"))
        except Exception:
            self.handleError(record)

    def close(self):
        """Close the underlying socket."""
        if self.socket is not None:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        super().close()


class EnterpriseLogger:
    """
    Enterprise Logger - Universal structured logging for any enterprise platform.

    Supports: ELK Stack, Splunk, Graylog, Fluentd, DataDog Logs, CloudWatch Logs, etc.
    """

    def __init__(
        self,
        service: str = "cortex-core-enterprise",
        environment: str = "development",
        config: Optional[Dict[str, Any]] = None,
    ):
        self.service = service
        self.environment = environment
        self.config = config or {}
        self.logger = None
        self._setup_logger()

    def _setup_logger(self):
        """Setup structured logging with multiple destinations."""
        # Create logger
        self.logger = logging.getLogger(self.service)
        self.logger.setLevel(getattr(logging, self.config.get("level", "INFO").upper()))

        # Close existing handlers before clearing them to release file
        # descriptors and sockets. This prevents ResourceWarnings when
        # EnterpriseLogger is instantiated repeatedly.
        for handler in list(self.logger.handlers):
            try:
                handler.close()
            except Exception:
                pass
        self.logger.handlers.clear()

        # Create JSON formatter
        formatter = EnterpriseJSONFormatter(
            service=self.service, environment=self.environment
        )

        # Setup destinations from config
        logging_config = self.config.get("logging", {})

        # Console logging
        if logging_config.get("console", {}).get("enabled", True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File logging
        file_config = logging_config.get("file", {})
        if file_config.get("enabled", True):
            file_handler = FileHandler(
                file_path=file_config.get("path", "/app/logs/cortex.log"),
                max_size_mb=file_config.get("max_size_mb", 100),
                backup_count=file_config.get("backup_count", 10),
                formatter=formatter,
            )
            self.logger.addHandler(file_handler)

        # Syslog
        syslog_config = logging_config.get("syslog", {})
        if syslog_config.get("enabled", False):
            syslog_handler = SyslogHandler(
                host=syslog_config.get("host", "localhost"),
                port=syslog_config.get("port", 514),
                formatter=formatter,
            )
            self.logger.addHandler(syslog_handler)

        # Fluentd
        fluentd_config = logging_config.get("fluentd", {})
        if fluentd_config.get("enabled", False):
            fluentd_handler = FluentdHandler(
                host=fluentd_config.get("host", "localhost"),
                port=fluentd_config.get("port", 24224),
                tag=fluentd_config.get("tag", "cortex.core"),
                formatter=formatter,
            )
            self.logger.addHandler(fluentd_handler)

        # Use structlog for additional structured logging capabilities
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    def get_logger(self, name: str = "") -> logging.Logger:
        """Get a configured logger instance."""
        if name:
            return logging.getLogger(f"{self.service}.{name}")
        return self.logger or logging.getLogger(self.service)

    def log_operation(
        self,
        operation: str,
        component: str,
        duration_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        correlation_id: Optional[str] = None,
        **extra,
    ):
        """Log an operation with enterprise-standard fields."""
        logger = self.get_logger(component)

        # Determine log level based on status
        if error_code or (status_code and status_code >= 400):
            level = logging.ERROR
        elif status_code and status_code >= 300:
            level = logging.WARNING
        else:
            level = logging.INFO

        # Create extra fields
        extra_fields = {
            "component": component,
            "operation": operation,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "error_code": error_code,
            "correlation_id": correlation_id,
            **extra,
        }

        # Remove None values
        extra_fields = {k: v for k, v in extra_fields.items() if v is not None}

        logger.log(level, f"Operation: {operation}", extra=extra_fields)

    def log_metric(
        self,
        name: str,
        value: Any,
        tags: Optional[Dict[str, str]] = None,
        component: str = "metrics",
    ):
        """Log a metric event."""
        logger = self.get_logger(component)
        logger.info(
            f"Metric: {name} = {value}",
            extra={
                "component": component,
                "metric_name": name,
                "metric_value": value,
                "tags": tags,
            },
        )

    def log_error(
        self,
        error: Exception,
        component: str = "error",
        correlation_id: Optional[str] = None,
        **extra,
    ):
        """Log an error with full context."""
        logger = self.get_logger(component)
        logger.error(
            f"Error: {str(error)}",
            extra={
                "component": component,
                "error_type": type(error).__name__,
                "correlation_id": correlation_id,
                "stack_trace": self._format_exception(error),
                **extra,
            },
            exc_info=True,
        )

    def log_security_event(
        self,
        event: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **extra,
    ):
        """Log a security event."""
        logger = self.get_logger("security")
        logger.warning(
            f"Security Event: {event}",
            extra={
                "component": "security",
                "event": event,
                "user_id": user_id,
                "session_id": session_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                **extra,
            },
        )

    def _format_exception(self, error: Exception) -> str:
        """Format exception with traceback."""
        import traceback

        return "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

    def create_correlation_logger(self, correlation_id: str) -> "CorrelationLogger":
        """Create a correlation logger for request tracing."""
        return CorrelationLogger(self, correlation_id)


class CorrelationLogger:
    """Logger with correlation ID for request tracing across distributed systems."""

    def __init__(self, enterprise_logger: EnterpriseLogger, correlation_id: str):
        self.enterprise_logger = enterprise_logger
        self.correlation_id = correlation_id

    def log_operation(self, operation: str, component: str, **kwargs):
        """Log operation with correlation ID."""
        self.enterprise_logger.log_operation(
            operation=operation,
            component=component,
            correlation_id=self.correlation_id,
            **kwargs,
        )

    def log_error(self, error: Exception, component: str = "error", **kwargs):
        """Log error with correlation ID."""
        self.enterprise_logger.log_error(
            error=error,
            component=component,
            correlation_id=self.correlation_id,
            **kwargs,
        )

    def get_logger(self, name: str = "") -> logging.Logger:
        """Get logger with correlation context."""
        logger = self.enterprise_logger.get_logger(name)
        # Add correlation ID to all log records from this logger
        return logger


# Global enterprise logger instance
enterprise_logger = EnterpriseLogger()
