"""Test Home Assistant logging util methods."""

import asyncio
from functools import partial
import inspect
import logging
import queue
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.core import (
    HomeAssistant,
    callback,
    is_callback,
    is_callback_check_partial,
)
from homeassistant.util import logging as logging_util

from tests.hass_fixtures import LogCapture, caplog, freezer, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported `hass` resolves via Depends()."""
    return 0


async def empty_log_queue() -> None:
    """Empty the log queue."""
    log_queue: queue.SimpleQueue = logging.root.handlers[0].queue
    while not log_queue.empty():
        await asyncio.sleep(0)


@test
async def logging_with_queue_handler() -> None:
    """Test logging with HomeAssistantQueueHandler."""

    simple_queue: queue.SimpleQueue = queue.SimpleQueue()
    handler = logging_util.HomeAssistantQueueHandler(simple_queue)

    log_record = logging.makeLogRecord({"msg": "Test Log Record"})

    handler.emit(log_record)

    with patch.object(handler, "enqueue", side_effect=asyncio.CancelledError):
        expect(lambda: handler.emit(log_record)).to_raise(asyncio.CancelledError)

    with patch.object(handler, "emit") as emit_mock:
        handler.handle(log_record)
        emit_mock.assert_called_once()

    with (
        patch.object(handler, "filter") as filter_mock,
        patch.object(handler, "emit") as emit_mock,
    ):
        filter_mock.return_value = False
        handler.handle(log_record)
        emit_mock.assert_not_called()

    with (
        patch.object(handler, "enqueue", side_effect=OSError),
        patch.object(handler, "handleError") as mock_handle_error,
    ):
        handler.emit(log_record)
        mock_handle_error.assert_called_once()

    handler.close()

    expect(simple_queue.get_nowait().msg).to_equal("Test Log Record")
    expect(simple_queue.empty()).to_be(True)


@test
async def migrate_log_handler(hass: HomeAssistant = Depends(hass)) -> None:
    """Test migrating log handlers."""

    logging_util.async_activate_log_queue_handler(hass)

    expect(len(logging.root.handlers)).to_equal(1)
    expect(
        isinstance(logging.root.handlers[0], logging_util.HomeAssistantQueueHandler)
    ).to_be(True)

    # Test that the close hook shuts down the queue handler's thread.
    listener_thread = logging.root.handlers[0].listener._thread
    expect(listener_thread.is_alive()).to_be(True)
    logging.root.handlers[0].close()
    expect(listener_thread.is_alive()).to_be(False)


@test
async def async_create_catching_coro(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test exception logging of wrapped coroutine."""

    async def job() -> None:
        raise Exception("This is a bad coroutine")  # noqa: TRY002

    hass.async_create_task(logging_util.async_create_catching_coro(job()))
    await hass.async_block_till_done()
    expect("This is a bad coroutine" in caplog.text).to_be(True)
    expect("in async_create_catching_coro" in caplog.text).to_be(True)


@test
def catch_log_exception() -> None:
    """Test it is still a callback after wrapping including partial."""

    async def async_meth() -> None:
        pass

    expect(
        inspect.iscoroutinefunction(
            logging_util.catch_log_exception(partial(async_meth), lambda: None)
        )
    ).to_be(True)

    @callback
    def callback_meth() -> None:
        pass

    expect(
        is_callback_check_partial(
            logging_util.catch_log_exception(partial(callback_meth), lambda: None)
        )
    ).to_be(True)

    def sync_meth() -> None:
        pass

    wrapped = logging_util.catch_log_exception(partial(sync_meth), lambda: None)

    expect(is_callback(wrapped)).to_be(False)
    expect(inspect.iscoroutinefunction(wrapped)).to_be(False)


@test
async def catch_log_exception_catches_and_logs() -> None:
    """Test it is still a callback after wrapping including partial."""
    saved_args: list[tuple[object, ...]] = []

    def save_args(*args: object) -> None:
        saved_args.append(args)

    async def async_meth() -> None:
        raise ValueError("failure async")

    func = logging_util.catch_log_exception(async_meth, save_args)
    await func("failure async passed")

    expect(saved_args).to_equal([("failure async passed",)])
    saved_args.clear()

    @callback
    def callback_meth() -> None:
        raise ValueError("failure callback")

    func = logging_util.catch_log_exception(callback_meth, save_args)
    func("failure callback passed")

    expect(saved_args).to_equal([("failure callback passed",)])
    saved_args.clear()

    def sync_meth() -> None:
        raise ValueError("failure sync")

    func = logging_util.catch_log_exception(sync_meth, save_args)
    func("failure sync passed")

    expect(saved_args).to_equal([("failure sync passed",)])


@test.cases(
    test.case(
        "under-threshold",
        logger1_count=4,
        logger1_expected_notices=0,
        logger2_count=0,
        logger2_expected_notices=0,
    ),
    test.case(
        "one-over",
        logger1_count=5,
        logger1_expected_notices=1,
        logger2_count=1,
        logger2_expected_notices=0,
    ),
    test.case(
        "one-spike",
        logger1_count=11,
        logger1_expected_notices=1,
        logger2_count=5,
        logger2_expected_notices=1,
    ),
    test.case(
        "both-spike",
        logger1_count=20,
        logger1_expected_notices=1,
        logger2_count=20,
        logger2_expected_notices=1,
    ),
)
@patch("homeassistant.util.logging.HomeAssistantQueueListener.MAX_LOGS_COUNT", 5)
@patch(
    "homeassistant.util.logging.HomeAssistantQueueListener.EXCLUDED_LOG_COUNT_MODULES",
    ["excluded"],
)
async def noisy_loggers(
    logger1_count: int,
    logger1_expected_notices: int,
    logger2_count: int,
    logger2_expected_notices: int,
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that noisy loggers all logged as warnings."""

    logging_util.async_activate_log_queue_handler(hass)
    logger1 = logging.getLogger("noisy1")
    logger2 = logging.getLogger("noisy2.module")
    logger_excluded = logging.getLogger("excluded.module")

    for _ in range(logger1_count):
        logger1.info("This is a log")

    for _ in range(logger2_count):
        logger2.info("This is another log")

    for _ in range(logging_util.HomeAssistantQueueListener.MAX_LOGS_COUNT + 1):
        logger_excluded.info("This log should not trigger a warning")

    await empty_log_queue()

    expect(
        caplog.text.count(
            "Module noisy1 is logging too frequently. 5 messages since last count"
        )
    ).to_equal(logger1_expected_notices)
    expect(
        caplog.text.count(
            "Module noisy2.module is logging too frequently. 5 messages since last count"
        )
    ).to_equal(logger2_expected_notices)
    # Ensure that the excluded module did not trigger a warning.
    expect(caplog.text.count("is logging too frequently")).to_equal(
        logger1_expected_notices + logger2_expected_notices
    )

    # Close the handler so the queue thread stops.
    logging.root.handlers[0].close()


@test
@patch("homeassistant.util.logging.HomeAssistantQueueListener.MAX_LOGS_COUNT", 1)
async def noisy_loggers_ignores_self(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that the noisy loggers warning does not trigger a warning for its own module."""

    logging_util.async_activate_log_queue_handler(hass)
    logger1 = logging.getLogger("noisy_module1")
    logger2 = logging.getLogger("noisy_module2")
    logger3 = logging.getLogger("noisy_module3")

    logger1.info("This is a log")
    logger2.info("This is a log")
    logger3.info("This is a log")

    await empty_log_queue()
    expect(caplog.text.count("logging too frequently")).to_equal(3)

    # Close the handler so the queue thread stops.
    logging.root.handlers[0].close()


@test
@patch("homeassistant.util.logging.HomeAssistantQueueListener.MAX_LOGS_COUNT", 5)
async def noisy_loggers_ignores_lower_than_info(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that noisy loggers all logged as warnings, except for levels lower than INFO."""

    logging_util.async_activate_log_queue_handler(hass)
    logger = logging.getLogger("noisy_module")

    for _ in range(5):
        logger.debug("This is a log")

    await empty_log_queue()
    expected_warning = "Module noisy_module is logging too frequently"
    expect(caplog.text.count(expected_warning)).to_equal(0)

    logger.info("This is a log")
    logger.info("This is a log")
    logger.warning("This is a log")
    logger.error("This is a log")
    logger.critical("This is a log")

    await empty_log_queue()
    expect(caplog.text.count(expected_warning)).to_equal(1)

    # Close the handler so the queue thread stops.
    logging.root.handlers[0].close()


@test
@patch("homeassistant.util.logging.HomeAssistantQueueListener.MAX_LOGS_COUNT", 3)
async def noisy_loggers_counters_reset(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test that noisy logger counters reset periodically."""

    logging_util.async_activate_log_queue_handler(hass)
    logger = logging.getLogger("noisy_module")

    expected_warning = "Module noisy_module is logging too frequently"

    # Do multiple iterations to ensure the reset is periodic.
    for _ in range(logging_util.HomeAssistantQueueListener.MAX_LOGS_COUNT * 2):
        logger.info("This is log 0")
        await empty_log_queue()

        freezer.tick(
            logging_util.HomeAssistantQueueListener.LOG_COUNTS_RESET_INTERVAL + 1
        )

        logger.info("This is log 1")
        await empty_log_queue()
        expect(caplog.text.count(expected_warning)).to_equal(0)

    logger.info("This is log 2")
    logger.info("This is log 3")
    await empty_log_queue()
    expect(caplog.text.count(expected_warning)).to_equal(1)
    # Close the handler so the queue thread stops.
    logging.root.handlers[0].close()
