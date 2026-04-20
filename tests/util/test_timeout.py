"""Test Home Assistant timeout handler."""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
import re
import time

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.util.timeout import TimeoutManager

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported `hass` resolves via Depends()."""
    return 0


@asynccontextmanager
async def _async_raises(
    exc_type: type[BaseException], match: str | None = None
) -> AsyncIterator[None]:
    """Assert the body raises ``exc_type``.

    Equivalent of ``pytest.raises`` for ``async with`` usage — Tryke's
    ``expect(...).to_raise`` only handles sync callables, so this stand-in
    covers the ``async with pytest.raises(...)`` conversion.
    """
    try:
        yield
    except exc_type as exc:
        if match is not None and not re.search(match, str(exc)):
            raise AssertionError(
                f"exception {exc_type.__name__} did not match {match!r}: {exc}"
            ) from None
        return
    raise AssertionError(f"did not raise {exc_type.__name__}")


async def _assert_raises(
    exc_type: type[BaseException], awaitable: Callable[[], Awaitable[object]]
) -> None:
    """Await a callable and assert it raises ``exc_type``."""
    try:
        await awaitable()
    except exc_type:
        return
    raise AssertionError(f"did not raise {exc_type.__name__}")


@test
async def simple_global_timeout() -> None:
    """Test a simple global timeout."""
    timeout = TimeoutManager()

    async with _async_raises(TimeoutError), timeout.async_timeout(0.1):
        await asyncio.sleep(0.3)


@test
async def simple_global_timeout_with_executor_job(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple global timeout with executor job."""
    timeout = TimeoutManager()

    async with _async_raises(TimeoutError), timeout.async_timeout(0.1):
        await hass.async_add_executor_job(time.sleep, 0.2)


@test
async def simple_global_timeout_freeze() -> None:
    """Test a simple global timeout freeze."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2), timeout.async_freeze():
        await asyncio.sleep(0.3)


@test
async def simple_global_timeout_cancel_message() -> None:
    """Test a simple global timeout cancel message."""
    timeout = TimeoutManager()

    with suppress(TimeoutError):
        async with timeout.async_timeout(0.1, cancel_message="Test"):
            async with _async_raises(
                asyncio.CancelledError, match="Global task timeout: Test"
            ):
                await asyncio.sleep(0.3)


@test
async def simple_zone_timeout_freeze_inside_executor_job(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple zone timeout freeze inside an executor job."""
    timeout = TimeoutManager()

    def _some_sync_work() -> None:
        with timeout.freeze("recorder"):
            time.sleep(0.3)

    async with (
        timeout.async_timeout(1.0),
        timeout.async_timeout(0.2, zone_name="recorder"),
    ):
        await hass.async_add_executor_job(_some_sync_work)


@test
async def simple_global_timeout_freeze_inside_executor_job(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple global timeout freeze inside an executor job."""
    timeout = TimeoutManager()

    def _some_sync_work() -> None:
        with timeout.freeze():
            time.sleep(0.3)

    async with timeout.async_timeout(0.2):
        await hass.async_add_executor_job(_some_sync_work)


@test
async def mix_global_timeout_freeze_and_zone_freeze_inside_executor_job(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple global timeout freeze inside an executor job."""
    timeout = TimeoutManager()

    def _some_sync_work() -> None:
        with timeout.freeze("recorder"):
            time.sleep(0.3)

    async with (
        timeout.async_timeout(0.1),
        timeout.async_timeout(0.2, zone_name="recorder"),
    ):
        await hass.async_add_executor_job(_some_sync_work)


@test
async def mix_global_timeout_freeze_and_zone_freeze_different_order(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple global timeout freeze inside an executor job before timeout was set."""
    timeout = TimeoutManager()

    def _some_sync_work() -> None:
        with timeout.freeze("recorder"):
            time.sleep(0.4)

    async with timeout.async_timeout(0.1):
        hass.async_add_executor_job(_some_sync_work)
        async with timeout.async_timeout(0.2, zone_name="recorder"):
            await asyncio.sleep(0.3)


@test
async def mix_global_timeout_freeze_and_zone_freeze_other_zone_inside_executor_job(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple global timeout freeze other zone inside an executor job."""
    timeout = TimeoutManager()

    def _some_sync_work() -> None:
        with timeout.freeze("not_recorder"):
            time.sleep(0.3)

    async with (
        _async_raises(TimeoutError),
        timeout.async_timeout(0.1),
        timeout.async_timeout(0.2, zone_name="recorder"),
        timeout.async_timeout(0.2, zone_name="not_recorder"),
    ):
        await hass.async_add_executor_job(_some_sync_work)


@test
async def mix_global_timeout_freeze_and_zone_freeze_inside_executor_job_second_job_outside_zone_context(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple global timeout freeze inside an executor job with second job outside of zone context."""
    timeout = TimeoutManager()

    def _some_sync_work() -> None:
        with timeout.freeze("recorder"):
            time.sleep(0.3)

    async with _async_raises(TimeoutError), timeout.async_timeout(0.1):
        async with timeout.async_timeout(0.2, zone_name="recorder"):
            await hass.async_add_executor_job(_some_sync_work)
        await hass.async_add_executor_job(time.sleep, 0.2)


@test
async def simple_global_timeout_freeze_with_executor_job(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple global timeout freeze with executor job."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2), timeout.async_freeze():
        await hass.async_add_executor_job(time.sleep, 0.3)


@test
async def simple_global_timeout_does_not_leak_upward(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a global timeout does not leak upward."""
    timeout = TimeoutManager()
    current_task = asyncio.current_task()
    assert current_task is not None
    cancelling_inside_timeout = None

    async with _async_raises(asyncio.TimeoutError), timeout.async_timeout(0.1):
        cancelling_inside_timeout = current_task.cancelling()
        await asyncio.sleep(0.3)

    expect(cancelling_inside_timeout).to_equal(0)
    # After the context manager exits, the task should no longer be cancelling.
    expect(current_task.cancelling()).to_equal(0)


@test
async def simple_global_timeout_does_swallow_cancellation(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a global timeout does not swallow cancellation."""
    timeout = TimeoutManager()
    current_task = asyncio.current_task()
    assert current_task is not None
    cancelling_inside_timeout: int | None = None

    async def task_with_timeout() -> None:
        nonlocal cancelling_inside_timeout
        new_task = asyncio.current_task()
        assert new_task is not None
        async with _async_raises(asyncio.TimeoutError):
            cancelling_inside_timeout = new_task.cancelling()
            async with timeout.async_timeout(0.1):
                await asyncio.sleep(0.3)

    # After the context manager exits, the task should no longer be cancelling.
    expect(current_task.cancelling()).to_equal(0)

    task = asyncio.create_task(task_with_timeout())
    await asyncio.sleep(0)
    task.cancel()
    expect(task.cancelling()).to_equal(1)

    expect(cancelling_inside_timeout).to_equal(0)
    # Cancellation should not leak into the current task.
    expect(current_task.cancelling()).to_equal(0)
    # Cancellation should not be swallowed if the task is cancelled and it
    # also times out.
    await asyncio.sleep(0)
    await _assert_raises(asyncio.CancelledError, lambda: task)
    expect(task.cancelling()).to_equal(1)


@test
async def simple_global_timeout_freeze_reset() -> None:
    """Test a simple global timeout freeze reset."""
    timeout = TimeoutManager()

    async with _async_raises(TimeoutError), timeout.async_timeout(0.2):
        async with timeout.async_freeze():
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.2)


@test
async def simple_zone_timeout() -> None:
    """Test a simple zone timeout."""
    timeout = TimeoutManager()

    async with _async_raises(TimeoutError), timeout.async_timeout(0.1, "test"):
        await asyncio.sleep(0.3)


@test
async def simple_zone_timeout_cancel_message() -> None:
    """Test a simple zone timeout cancel message."""
    timeout = TimeoutManager()

    with suppress(TimeoutError):
        async with timeout.async_timeout(0.1, "test", cancel_message="Test"):
            async with _async_raises(
                asyncio.CancelledError, match="Zone timeout: Test"
            ):
                await asyncio.sleep(0.3)


@test
async def simple_zone_timeout_does_not_leak_upward(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a zone timeout does not leak upward."""
    timeout = TimeoutManager()
    current_task = asyncio.current_task()
    assert current_task is not None
    cancelling_inside_timeout = None

    async with (
        _async_raises(asyncio.TimeoutError),
        timeout.async_timeout(0.1, "test"),
    ):
        cancelling_inside_timeout = current_task.cancelling()
        await asyncio.sleep(0.3)

    expect(cancelling_inside_timeout).to_equal(0)
    # After the context manager exits, the task should no longer be cancelling.
    expect(current_task.cancelling()).to_equal(0)


@test
async def simple_zone_timeout_does_swallow_cancellation(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a zone timeout does not swallow cancellation."""
    timeout = TimeoutManager()
    current_task = asyncio.current_task()
    assert current_task is not None
    cancelling_inside_timeout: int | None = None

    async def task_with_timeout() -> None:
        nonlocal cancelling_inside_timeout
        new_task = asyncio.current_task()
        assert new_task is not None
        async with (
            _async_raises(asyncio.TimeoutError),
            timeout.async_timeout(0.1, "test"),
        ):
            cancelling_inside_timeout = current_task.cancelling()
            await asyncio.sleep(0.3)

    # After the context manager exits, the task should no longer be cancelling.
    expect(current_task.cancelling()).to_equal(0)

    task = asyncio.create_task(task_with_timeout())
    await asyncio.sleep(0)
    task.cancel()
    expect(task.cancelling()).to_equal(1)

    # Cancellation should not leak into the current task.
    expect(cancelling_inside_timeout).to_equal(0)
    expect(current_task.cancelling()).to_equal(0)
    # Cancellation should not be swallowed if the task is cancelled and it
    # also times out.
    await asyncio.sleep(0)
    await _assert_raises(asyncio.CancelledError, lambda: task)
    expect(task.cancelling()).to_equal(1)


@test
async def multiple_zone_timeout() -> None:
    """Test a simple zone timeout."""
    timeout = TimeoutManager()

    async with (
        _async_raises(TimeoutError),
        timeout.async_timeout(0.1, "test"),
        timeout.async_timeout(0.5, "test"),
    ):
        await asyncio.sleep(0.3)


@test
async def different_zone_timeout() -> None:
    """Test a simple zone timeout."""
    timeout = TimeoutManager()

    async with (
        _async_raises(TimeoutError),
        timeout.async_timeout(0.1, "test"),
        timeout.async_timeout(0.5, "other"),
    ):
        await asyncio.sleep(0.3)


@test
async def simple_zone_timeout_freeze() -> None:
    """Test a simple zone timeout freeze."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2, "test"), timeout.async_freeze("test"):
        await asyncio.sleep(0.3)


@test
async def simple_zone_timeout_freeze_without_timeout() -> None:
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.1, "test"), timeout.async_freeze("test"):
        await asyncio.sleep(0.3)


@test
async def simple_zone_timeout_freeze_reset() -> None:
    """Test a simple zone timeout freeze reset."""
    timeout = TimeoutManager()

    async with _async_raises(TimeoutError), timeout.async_timeout(0.2, "test"):
        async with timeout.async_freeze("test"):
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.2, "test")


@test
async def mix_zone_timeout_freeze_and_global_freeze() -> None:
    """Test a mix zone timeout freeze and global freeze."""
    timeout = TimeoutManager()

    async with (
        timeout.async_timeout(0.2, "test"),
        timeout.async_freeze("test"),
        timeout.async_freeze(),
    ):
        await asyncio.sleep(0.3)


@test
async def mix_global_and_zone_timeout_freeze() -> None:
    """Test a mix zone timeout freeze and global freeze."""
    timeout = TimeoutManager()

    async with (
        timeout.async_timeout(0.2, "test"),
        timeout.async_freeze(),
        timeout.async_freeze("test"),
    ):
        await asyncio.sleep(0.3)


@test
async def mix_zone_timeout_freeze() -> None:
    """Test a mix zone timeout global freeze."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.2, "test"), timeout.async_freeze():
        await asyncio.sleep(0.3)


@test
async def mix_zone_timeout() -> None:
    """Test a mix zone timeout global."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.1):
        with suppress(TimeoutError):
            async with timeout.async_timeout(0.2, "test"):
                await asyncio.sleep(0.4)


@test
async def mix_zone_timeout_trigger_global() -> None:
    """Test a mix zone timeout global with trigger it."""
    timeout = TimeoutManager()

    async with _async_raises(TimeoutError), timeout.async_timeout(0.1):
        with suppress(TimeoutError):
            async with timeout.async_timeout(0.1, "test"):
                await asyncio.sleep(0.3)

        await asyncio.sleep(0.3)


@test
async def mix_zone_timeout_trigger_global_cool_down() -> None:
    """Test a mix zone timeout global with trigger it with cool_down."""
    timeout = TimeoutManager()

    async with timeout.async_timeout(0.1, cool_down=0.3):
        with suppress(TimeoutError):
            async with timeout.async_timeout(0.1, "test"):
                await asyncio.sleep(0.3)

        await asyncio.sleep(0.2)

    # Cleanup lingering (cool_down) task after test is done.
    await asyncio.sleep(0.3)


@test
async def simple_zone_timeout_freeze_without_timeout_cleanup(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    async def background() -> None:
        async with timeout.async_freeze("test"):
            await asyncio.sleep(0.4)

    async with timeout.async_timeout(0.1):
        hass.async_create_task(background())
        await asyncio.sleep(0.2)


@test
async def simple_zone_timeout_freeze_without_timeout_cleanup2(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    async def background() -> None:
        async with timeout.async_freeze("test"):
            await asyncio.sleep(0.2)

    async with _async_raises(TimeoutError), timeout.async_timeout(0.1):
        hass.async_create_task(background())
        await asyncio.sleep(0.3)


@test
async def simple_zone_timeout_freeze_without_timeout_exception() -> None:
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    async with _async_raises(TimeoutError), timeout.async_timeout(0.1):
        with suppress(RuntimeError):
            async with timeout.async_freeze("test"):
                raise RuntimeError

        await asyncio.sleep(0.4)


@test
async def simple_zone_timeout_zone_with_timeout_exception() -> None:
    """Test a simple zone timeout freeze on a zone that does not have a timeout set."""
    timeout = TimeoutManager()

    async with _async_raises(TimeoutError), timeout.async_timeout(0.1):
        with suppress(RuntimeError):
            async with timeout.async_timeout(0.3, "test"):
                raise RuntimeError

        await asyncio.sleep(0.3)


@test
async def multiple_global_freezes(hass: HomeAssistant = Depends(hass)) -> None:
    """Test multiple global freezes."""
    timeout = TimeoutManager()

    async def background(delay: float) -> None:
        async with timeout.async_freeze():
            await asyncio.sleep(delay)

    async with timeout.async_timeout(0.1):
        task = hass.async_create_task(background(0.2))
        async with timeout.async_freeze():
            await asyncio.sleep(0.1)
    await task

    async with timeout.async_timeout(0.1):
        task = hass.async_create_task(background(0.2))
        async with timeout.async_freeze():
            await asyncio.sleep(0.3)
    await task
