"""Test Home Assistant executor util."""

import concurrent.futures
import time
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.util import executor
from homeassistant.util.executor import InterruptibleThreadPoolExecutor

from tests.hass_fixtures import LogCapture, caplog


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported `caplog` resolves via Depends()."""
    return 0


@test
async def executor_shutdown_can_interrupt_threads(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that the executor shutdown can interrupt threads."""

    iexecutor = InterruptibleThreadPoolExecutor()

    def _loop_sleep_in_executor() -> None:
        while True:
            time.sleep(0.1)

    sleep_futures = [iexecutor.submit(_loop_sleep_in_executor) for _ in range(100)]

    iexecutor.shutdown()

    for future in sleep_futures:
        raised: BaseException | None = None
        try:
            future.result()
        except (concurrent.futures.CancelledError, SystemExit) as exc:
            raised = exc
        expect(raised).not_.to_be(None)

    expect("is still running at shutdown" in caplog.text).to_be(True)
    expect("time.sleep(0.1)" in caplog.text).to_be(True)


@test
async def executor_shutdown_only_logs_max_attempts(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that the executor shutdown will only log max attempts."""

    iexecutor = InterruptibleThreadPoolExecutor()

    def _loop_sleep_in_executor() -> None:
        time.sleep(0.2)

    iexecutor.submit(_loop_sleep_in_executor)

    with patch.object(executor, "EXECUTOR_SHUTDOWN_TIMEOUT", 0.3):
        iexecutor.shutdown()

    expect("time.sleep(0.2)" in caplog.text).to_be(True)
    expect("is still running at shutdown" in caplog.text).to_be(True)
    iexecutor.shutdown()


@test
async def executor_shutdown_does_not_log_shutdown_on_first_attempt(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that the executor shutdown does not log on first attempt."""

    iexecutor = InterruptibleThreadPoolExecutor()

    def _do_nothing() -> None:
        return

    for _ in range(5):
        iexecutor.submit(_do_nothing)

    iexecutor.shutdown()

    expect("is still running at shutdown" not in caplog.text).to_be(True)


@test
async def overall_timeout_reached(caplog: LogCapture = Depends(caplog)) -> None:
    """Test that shutdown moves on when the overall timeout is reached."""

    def _loop_sleep_in_executor() -> None:
        time.sleep(1)

    with patch.object(executor, "EXECUTOR_SHUTDOWN_TIMEOUT", 0.5):
        iexecutor = InterruptibleThreadPoolExecutor()
        for _ in range(6):
            iexecutor.submit(_loop_sleep_in_executor)
        start = time.monotonic()
        iexecutor.shutdown()
        finish = time.monotonic()

    # Ideally execution time (finish - start) should be < 1.2 sec.
    # CI tests might not run in an ideal environment and timing might
    # not be accurate, so we let this test pass
    # if the duration is below 3 seconds.
    expect(finish - start < 3.0).to_be(True)

    iexecutor.shutdown()
