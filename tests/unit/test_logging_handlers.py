"""
Tests for the close() methods on socket-based log handlers.

Real code only. No mocks, no network, no threads.
"""

import logging

from cortex_core.integration.logging import (
    FluentdHandler,
    SyslogHandler,
)


class _RaisingSocket:
    """A real socket-like object whose close() raises."""

    def __init__(self):
        self.close_calls = 0

    def close(self):
        self.close_calls += 1
        raise OSError("intentional close failure")


def _make_record(msg="test"):
    return logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )


def test_syslog_close_swallows_socket_error():
    """SyslogHandler.close must swallow a socket.close error (logging.py 171-172)."""
    handler = SyslogHandler(host="127.0.0.1", port=0)
    bad = _RaisingSocket()
    handler.socket = bad

    handler.close()

    assert bad.close_calls == 1
    assert handler.socket is None


def test_syslog_close_no_socket_is_safe():
    handler = SyslogHandler(host="127.0.0.1", port=0)
    assert handler.socket is None
    handler.close()
    assert handler.socket is None


def test_fluentd_close_swallows_socket_error():
    """FluentdHandler.close must swallow a socket.close error (logging.py 218-222)."""
    handler = FluentdHandler(host="127.0.0.1", port=0, tag="cortex.core")
    bad = _RaisingSocket()
    handler.socket = bad

    handler.close()

    assert bad.close_calls == 1
    assert handler.socket is None


def test_fluentd_close_no_socket_is_safe():
    handler = FluentdHandler(host="127.0.0.1", port=0, tag="cortex.core")
    assert handler.socket is None
    handler.close()
    assert handler.socket is None


def test_setup_logger_swallows_close_exception():
    """_setup_logger must survive a handler whose close() raises
    (logging.py 253-254).
    """
    import logging as _logging

    from cortex_core.integration.logging import EnterpriseLogger

    class _RaisingCloseHandler(_logging.Handler):
        """Real logging.Handler whose close() raises, to hit the except branch."""

        def __init__(self):
            super().__init__()
            self.close_calls = 0

        def emit(self, record):
            pass

        def close(self):
            self.close_calls += 1
            try:
                super().close()
            finally:
                raise RuntimeError("intentional close failure")

    service = "cortex-core-enterprise"
    bad = _RaisingCloseHandler()
    target_logger = _logging.getLogger(service)
    target_logger.handlers.append(bad)
    try:
        el = EnterpriseLogger(service=service, environment="test")
        assert (
            bad.close_calls == 1
        ), "_setup_logger did not attempt to close the existing handler"
        assert (
            bad not in el.logger.handlers
        ), "stale handler remained after _setup_logger cleared the list"
    finally:
        if bad in target_logger.handlers:
            target_logger.handlers.remove(bad)
