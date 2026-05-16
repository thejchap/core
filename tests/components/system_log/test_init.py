"""Test system log component."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
import logging
import re
import traceback
from typing import Any
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import system_log
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.setup import async_setup_component

from tests.common import async_capture_events
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
)
from tests.typing import WebSocketGenerator

_LOGGER = logging.getLogger("test_logger")
BASIC_CONFIG = {"system_log": {"max_entries": 2}}


class _FormattingHandler(logging.Handler):
    """Force exc_text/message population on records, mimicking pytest's logging plugin.

    Under pytest, the auto-attached LogCaptureHandler formats every record,
    which sets ``record.exc_text`` / ``record.message`` as a side effect on
    the shared LogRecord. Tryke has no equivalent autouse, so we install
    this no-op formatting handler to drive the same side effect.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.format(record)
        except Exception:  # noqa: BLE001
            pass


@fixture
def _format_records() -> Any:
    """Install a root-logger handler that formats every record."""
    handler = _FormattingHandler()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        yield handler
    finally:
        root.removeHandler(handler)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _formatter: Any = Depends(_format_records),
) -> HomeAssistant:
    return hass


async def get_error_log(hass_ws_client):
    """Fetch all entries from system_log via the API."""
    client = await hass_ws_client()
    await client.send_json({"id": 5, "type": "system_log/list"})

    msg = await client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["success"]).to_be(True)
    return msg["result"]


def _generate_and_log_exception(exception, log):
    try:
        raise Exception(exception)  # noqa: TRY002, TRY301
    except Exception:
        _LOGGER.exception(log)


def find_log(logs, level):
    """Return log with specific level."""
    if not isinstance(level, tuple):
        level = (level,)
    log = next(
        (log for log in logs if log["level"] in level and log["name"] != "asyncio"),
        None,
    )
    expect(log).not_.to_be(None)
    return log


def assert_log(log, exception, message, level):
    """Assert that specified values are in a specific log entry."""
    if not isinstance(message, list):
        message = [message]

    expect(log["name"]).to_equal("test_logger")
    expect(exception in log["exception"]).to_be(True)
    expect(log["message"]).to_equal(message)
    expect(log["level"]).to_equal(level)
    expect("timestamp" in log).to_be(True)


class WatchLogErrorHandler(system_log.LogErrorHandler):
    """WatchLogErrorHandler that watches for a message."""

    instances: list[WatchLogErrorHandler] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize HASSQueueListener."""
        super().__init__(*args, **kwargs)
        self.watch_message: str | None = None
        self.watch_event: asyncio.Event | None = asyncio.Event()
        WatchLogErrorHandler.instances.append(self)

    def add_watcher(self, match: str) -> Awaitable:
        """Add a watcher."""
        self.watch_event = asyncio.Event()
        self.watch_message = match
        return self.watch_event.wait()

    def handle(self, record: logging.LogRecord) -> None:
        """Handle a logging record."""
        super().handle(record)
        message = getattr(record, "message", None) or record.getMessage()
        if message in self.watch_message:
            self.watch_event.set()


async def async_setup_system_log(
    hass: HomeAssistant, config: ConfigType
) -> WatchLogErrorHandler:
    """Set up the system_log component."""
    WatchLogErrorHandler.instances = []
    with patch(
        "homeassistant.components.system_log.LogErrorHandler", WatchLogErrorHandler
    ):
        await async_setup_component(hass, system_log.DOMAIN, config)
        await hass.async_block_till_done()

    expect(len(WatchLogErrorHandler.instances)).to_equal(1)
    return WatchLogErrorHandler.instances.pop()


@test
async def normal_logs(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that debug and info are not logged."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()
    _LOGGER.debug("debug")
    _LOGGER.info("Info")

    # Assert done by get_error_log
    logs = await get_error_log(hass_ws_client)
    expect(len([msg for msg in logs if msg["level"] in ("DEBUG", "INFO")])).to_equal(0)


@test
async def exception(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that exceptions are logged and retrieved correctly."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()

    _generate_and_log_exception("exception message", "log message")
    log = find_log(await get_error_log(hass_ws_client), "ERROR")
    expect(log).not_.to_be(None)
    assert_log(log, "exception message", "log message", "ERROR")


@test
async def warning(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that warning are logged and retrieved correctly."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()
    _LOGGER.warning("Warning message")

    log = find_log(await get_error_log(hass_ws_client), "WARNING")
    assert_log(log, "", "Warning message", "WARNING")


@test
async def warning_good_format(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that warning with good format arguments are logged and retrieved correctly."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()
    _LOGGER.warning("Warning message: %s", "test")
    await hass.async_block_till_done()

    log = find_log(await get_error_log(hass_ws_client), "WARNING")
    assert_log(log, "", "Warning message: test", "WARNING")


@test
async def warning_missing_format_args(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that warning with missing format arguments are logged and retrieved correctly."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()
    _LOGGER.warning("Warning message missing a format arg %s")
    await hass.async_block_till_done()

    log = find_log(await get_error_log(hass_ws_client), "WARNING")
    assert_log(log, "", ["Warning message missing a format arg %s"], "WARNING")


@test
async def error_test(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that errors are logged and retrieved correctly."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()

    _LOGGER.error("Error message")

    log = find_log(await get_error_log(hass_ws_client), "ERROR")
    assert_log(log, "", "Error message", "ERROR")


@test
async def config_not_fire_event(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that errors are not posted as events with default config."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()
    events = []

    @callback
    def event_listener(event):
        """Listen to events of type system_log_event."""
        events.append(event)

    hass.bus.async_listen(system_log.EVENT_SYSTEM_LOG, event_listener)

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    expect(len(events)).to_equal(0)


@test
async def error_posted_as_event(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that error are posted as events."""
    watcher = await async_setup_system_log(
        hass, {"system_log": {"max_entries": 2, "fire_event": True}}
    )
    wait_empty = watcher.add_watcher("Error message")

    events = async_capture_events(hass, system_log.EVENT_SYSTEM_LOG)

    _LOGGER.error("Error message")
    await wait_empty
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    expect(len(events)).to_equal(1)
    assert_log(events[0].data, "", "Error message", "ERROR")


@test
async def critical(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that critical are logged and retrieved correctly."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()

    _LOGGER.critical("Critical message")

    log = find_log(await get_error_log(hass_ws_client), "CRITICAL")
    assert_log(log, "", "Critical message", "CRITICAL")


@test
async def remove_older_logs(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that older logs are rotated out."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()
    _LOGGER.error("Error message 1")
    _LOGGER.error("Error message 2")
    _LOGGER.error("Error message 3")
    await hass.async_block_till_done()
    log = await get_error_log(hass_ws_client)
    assert_log(log[0], "", "Error message 3", "ERROR")
    assert_log(log[1], "", "Error message 2", "ERROR")


def log_msg(nr=2):
    """Log an error at same line."""
    _LOGGER.error("Error message %s", nr)


@test
async def dedupe_logs(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that duplicate log entries are dedupe."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()
    _LOGGER.error("Error message 1")
    log_msg()
    log_msg("2-2")
    _LOGGER.error("Error message 3")

    log = await get_error_log(hass_ws_client)
    assert_log(log[0], "", "Error message 3", "ERROR")
    expect(log[1]["count"]).to_equal(2)
    assert_log(log[1], "", ["Error message 2", "Error message 2-2"], "ERROR")

    log_msg()
    log = await get_error_log(hass_ws_client)
    assert_log(log[0], "", ["Error message 2", "Error message 2-2"], "ERROR")
    expect(log[0]["timestamp"] > log[0]["first_occurred"]).to_be(True)

    log_msg("2-3")
    log_msg("2-4")
    log_msg("2-5")
    log_msg("2-6")

    log = await get_error_log(hass_ws_client)
    assert_log(
        log[0],
        "",
        [
            "Error message 2-2",
            "Error message 2-3",
            "Error message 2-4",
            "Error message 2-5",
            "Error message 2-6",
        ],
        "ERROR",
    )


@test
async def clear_logs(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that the log can be cleared via a service call."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()
    _LOGGER.error("Error message")

    await hass.services.async_call(system_log.DOMAIN, system_log.SERVICE_CLEAR, {})
    await hass.async_block_till_done()
    # Assert done by get_error_log
    await get_error_log(hass_ws_client)


@test
async def write_log(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test that error propagates to logger."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()

    logger = MagicMock()
    with patch("logging.getLogger", return_value=logger) as mock_logging:
        await hass.services.async_call(
            system_log.DOMAIN, system_log.SERVICE_WRITE, {"message": "test_message"}
        )
        await hass.async_block_till_done()
    mock_logging.assert_called_once_with("homeassistant.components.system_log.external")
    expect(logger.method_calls[0]).to_equal(("error", ("test_message",)))


@test
async def write_choose_logger(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test that correct logger is chosen."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()

    with patch("logging.getLogger") as mock_logging:
        await hass.services.async_call(
            system_log.DOMAIN,
            system_log.SERVICE_WRITE,
            {"message": "test_message", "logger": "myLogger"},
        )
        await hass.async_block_till_done()
    mock_logging.assert_called_once_with("myLogger")


@test
async def write_choose_level(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test that correct logger is chosen."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()

    logger = MagicMock()
    with patch("logging.getLogger", return_value=logger):
        await hass.services.async_call(
            system_log.DOMAIN,
            system_log.SERVICE_WRITE,
            {"message": "test_message", "level": "debug"},
        )
        await hass.async_block_till_done()
    expect(logger.method_calls[0]).to_equal(("debug", ("test_message",)))


@test
async def unknown_path(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test error logged from unknown path."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()
    _LOGGER.findCaller = MagicMock(return_value=("unknown_path", 0, None, None))
    _LOGGER.error("Error message")
    log = (await get_error_log(hass_ws_client))[0]
    expect(log["source"]).to_equal(["unknown_path", 0])


def get_frame(path: str, previous_frame: MagicMock | None) -> MagicMock:
    """Get log stack frame."""
    return MagicMock(
        f_back=previous_frame,
        f_code=MagicMock(co_filename=path),
        f_lineno=5,
    )


async def async_log_error_from_test_path(
    hass: HomeAssistant, path: str, watcher: WatchLogErrorHandler
) -> None:
    """Log error while mocking the path."""
    call_path = "internal_path.py"
    main_frame = get_frame("main_path/main.py", None)
    path_frame = get_frame(path, main_frame)
    call_path_frame = get_frame(call_path, path_frame)
    logger_frame = get_frame("venv_path/logging/log.py", call_path_frame)

    with (
        patch.object(
            _LOGGER, "findCaller", MagicMock(return_value=(call_path, 0, None, None))
        ),
        patch(
            "homeassistant.components.system_log.sys._getframe",
            return_value=logger_frame,
        ),
    ):
        wait_empty = watcher.add_watcher("Error message")
        _LOGGER.error("Error message")
        await wait_empty


@test
async def homeassistant_path(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test error logged from Home Assistant path."""

    with patch(
        "homeassistant.components.system_log.HOMEASSISTANT_PATH",
        new=["venv_path/homeassistant"],
    ):
        watcher = await async_setup_system_log(hass, BASIC_CONFIG)
        await async_log_error_from_test_path(
            hass, "venv_path/homeassistant/component/component.py", watcher
        )
        log = (await get_error_log(hass_ws_client))[0]
    expect(log["source"]).to_equal(["component/component.py", 5])


@test
async def config_path(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test error logged from config path."""

    with patch.object(hass.config, "config_dir", new="config"):
        watcher = await async_setup_system_log(hass, BASIC_CONFIG)

        await async_log_error_from_test_path(
            hass, "config/custom_component/test.py", watcher
        )
        log = (await get_error_log(hass_ws_client))[0]
    expect(log["source"]).to_equal(["custom_component/test.py", 5])


@test
async def raise_during_log_capture(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that exceptions are logged and retrieved correctly."""
    await async_setup_component(hass, system_log.DOMAIN, BASIC_CONFIG)
    await hass.async_block_till_done()

    class RaisesDuringRepr:
        """Class that raises during repr."""

        def __repr__(self):
            in_system_log = False
            for stack in traceback.extract_stack():
                if "homeassistant/components/system_log" in stack.filename:
                    in_system_log = True
                    break
            if in_system_log:
                raise ValueError("repr error")
            return "repr message"

    raise_during_repr = RaisesDuringRepr()

    _LOGGER.error("Raise during repr: %s", raise_during_repr)
    log = find_log(await get_error_log(hass_ws_client), "ERROR")
    expect(log).not_.to_be(None)
    assert_log(log, "", "Bad logger message: repr error", "ERROR")


@test
async def _figure_out_source(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test that source is figured out correctly.

    We have to test this directly for exception tracebacks since
    we cannot generate a trackback from a Home Assistant component
    in a test because the test is not a component.
    """
    try:
        raise ValueError("test")  # noqa: TRY301
    except ValueError as ex:
        exc_info = (type(ex), ex, ex.__traceback__)
    mock_record = MagicMock(
        pathname="figure_out_source is False",
        lineno=5,
        exc_info=exc_info,
    )
    regex_str = f"({__file__})"
    paths_re = re.compile(regex_str)
    file, line_no = system_log._figure_out_source(
        mock_record,
        paths_re,
        list(traceback.walk_tb(exc_info[2])),
    )
    expect(file).to_equal(__file__)
    expect(line_no != 5).to_be(True)

    entry = system_log.LogEntry(mock_record, paths_re, figure_out_source=False)
    expect(entry.source).to_equal(("figure_out_source is False", 5))


@test
async def formatting_exception(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test that exceptions are formatted correctly."""
    try:
        raise ValueError("test")  # noqa: TRY301
    except ValueError as ex:
        exc_info = (type(ex), ex, ex.__traceback__)
    mock_record = MagicMock(
        pathname="figure_out_source is False",
        lineno=5,
        exc_info=exc_info,
        exc_text=None,
    )
    regex_str = f"({__file__})"
    paths_re = re.compile(regex_str)

    mock_formatter = MagicMock(
        formatException=MagicMock(return_value="formatted exception")
    )
    entry = system_log.LogEntry(
        mock_record, paths_re, formatter=mock_formatter, figure_out_source=False
    )
    expect(entry.exception).to_equal("formatted exception")
    expect(mock_record.exc_text).to_equal("formatted exception")
