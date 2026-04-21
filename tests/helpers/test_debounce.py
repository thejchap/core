"""Tests for debounce."""

import asyncio
from datetime import timedelta
import logging
from typing import Any
from unittest.mock import AsyncMock, Mock
import weakref

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import debounce
from homeassistant.util.dt import utcnow

from tests.common import async_fire_time_changed
from tests.hass_fixtures import LogCapture, caplog, hass

_LOGGER = logging.getLogger(__name__)


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def immediate_works(hass: HomeAssistant = Depends(hass)) -> None:
    """Test immediate works."""
    calls: list[Any] = []
    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=True,
        function=AsyncMock(side_effect=lambda: calls.append(None)),
    )

    # Call when nothing happening
    await debouncer.async_call()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Call when cooldown active setting execute at end to True
    await debouncer.async_call()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Canceling debounce in cooldown
    debouncer.async_cancel()
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    before_job = debouncer._job

    # Call and let timer run out
    await debouncer.async_call()
    expect(len(calls)).to_equal(2)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)
    expect(debouncer._job).to_equal(before_job)

    # Test calling enabled timer if currently executing.
    await debouncer._execute_lock.acquire()
    await debouncer.async_call()
    expect(len(calls)).to_equal(2)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    debouncer._execute_lock.release()
    expect(debouncer._job.target).to_equal(debouncer.function)

    debouncer.async_shutdown()


@test
async def immediate_works_with_schedule_call(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test immediate works with scheduled calls."""
    calls: list[Any] = []
    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=True,
        function=AsyncMock(side_effect=lambda: calls.append(None)),
    )

    # Call when nothing happening
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Call when cooldown active setting execute at end to True
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Canceling debounce in cooldown
    debouncer.async_cancel()
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    before_job = debouncer._job

    # Call and let timer run out
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)
    expect(debouncer._job).to_equal(before_job)

    # Test calling enabled timer if currently executing.
    await debouncer._execute_lock.acquire()
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    debouncer._execute_lock.release()
    expect(debouncer._job.target).to_equal(debouncer.function)

    debouncer.async_shutdown()


@test
async def immediate_works_with_callback_function(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test immediate works with callback function."""
    calls: list[Any] = []
    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=True,
        function=callback(Mock(side_effect=lambda: calls.append(None))),
    )

    # Call when nothing happening
    await debouncer.async_call()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    debouncer.async_shutdown()


@test
async def immediate_works_with_executor_function(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test immediate works with executor function."""
    calls: list[Any] = []
    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=True,
        function=Mock(side_effect=lambda: calls.append(None)),
    )

    # Call when nothing happening
    await debouncer.async_call()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    debouncer.async_shutdown()


async def _expect_runtime_error_forced_raise(coro: Any) -> None:
    caught: Exception | None = None
    try:
        await coro
    except RuntimeError as exc:
        caught = exc
    expect(caught).not_.to_be_none()
    expect("forced_raise" in str(caught)).to_be(True)


@test
async def immediate_works_with_passed_callback_function_raises(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test immediate works with a callback function that raises."""
    calls: list[Any] = []

    @callback
    def _append_and_raise() -> None:
        calls.append(None)
        raise RuntimeError("forced_raise")

    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=True,
        function=_append_and_raise,
    )

    # Call when nothing happening
    await _expect_runtime_error_forced_raise(debouncer.async_call())
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Call when cooldown active setting execute at end to True
    await debouncer.async_call()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Canceling debounce in cooldown
    debouncer.async_cancel()
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    before_job = debouncer._job

    # Call and let timer run out
    await _expect_runtime_error_forced_raise(debouncer.async_call())
    expect(len(calls)).to_equal(2)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)
    expect(debouncer._job).to_equal(before_job)

    # Test calling enabled timer if currently executing.
    await debouncer._execute_lock.acquire()
    await debouncer.async_call()
    expect(len(calls)).to_equal(2)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    debouncer._execute_lock.release()
    expect(debouncer._job.target).to_equal(debouncer.function)

    debouncer.async_shutdown()


@test
async def immediate_works_with_passed_coroutine_raises(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test immediate works with a coroutine that raises."""
    calls: list[Any] = []

    async def _append_and_raise() -> None:
        calls.append(None)
        raise RuntimeError("forced_raise")

    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=True,
        function=_append_and_raise,
    )

    # Call when nothing happening
    await _expect_runtime_error_forced_raise(debouncer.async_call())
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Call when cooldown active setting execute at end to True
    await debouncer.async_call()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Canceling debounce in cooldown
    debouncer.async_cancel()
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    before_job = debouncer._job

    # Call and let timer run out
    await _expect_runtime_error_forced_raise(debouncer.async_call())
    expect(len(calls)).to_equal(2)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)
    expect(debouncer._job).to_equal(before_job)

    # Test calling enabled timer if currently executing.
    await debouncer._execute_lock.acquire()
    await debouncer.async_call()
    expect(len(calls)).to_equal(2)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    debouncer._execute_lock.release()
    expect(debouncer._job.target).to_equal(debouncer.function)

    debouncer.async_shutdown()


@test
async def not_immediate_works(hass: HomeAssistant = Depends(hass)) -> None:
    """Test immediate works."""
    calls: list[Any] = []
    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=False,
        function=AsyncMock(side_effect=lambda: calls.append(None)),
    )

    # Call when nothing happening
    await debouncer.async_call()
    expect(len(calls)).to_equal(0)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)

    # Call while still on cooldown
    await debouncer.async_call()
    expect(len(calls)).to_equal(0)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)

    # Canceling while on cooldown
    debouncer.async_cancel()
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)

    # Call and let timer run out
    await debouncer.async_call()
    expect(len(calls)).to_equal(0)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Reset debouncer
    debouncer.async_cancel()

    # Test calling enabled timer if currently executing.
    await debouncer._execute_lock.acquire()
    await debouncer.async_call()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    debouncer._execute_lock.release()
    expect(debouncer._job.target).to_equal(debouncer.function)

    debouncer.async_shutdown()


@test
async def not_immediate_works_schedule_call(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test immediate works with schedule call."""
    calls: list[Any] = []
    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=False,
        function=AsyncMock(side_effect=lambda: calls.append(None)),
    )

    # Call when nothing happening
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)

    # Call while still on cooldown
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)

    # Canceling while on cooldown
    debouncer.async_cancel()
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)

    # Call and let timer run out
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Reset debouncer
    debouncer.async_cancel()

    # Test calling enabled timer if currently executing.
    await debouncer._execute_lock.acquire()
    debouncer.async_schedule_call()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    debouncer._execute_lock.release()
    expect(debouncer._job.target).to_equal(debouncer.function)

    debouncer.async_shutdown()


@test
async def immediate_works_with_function_swapped(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test immediate works and we can change out the function."""
    calls: list[Any] = []

    one_function = AsyncMock(side_effect=lambda: calls.append(1))
    two_function = AsyncMock(side_effect=lambda: calls.append(2))

    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=True,
        function=one_function,
    )

    # Call when nothing happening
    await debouncer.async_call()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Call when cooldown active setting execute at end to True
    await debouncer.async_call()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    expect(debouncer._job.target).to_equal(debouncer.function)

    # Canceling debounce in cooldown
    debouncer.async_cancel()
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)

    before_job = debouncer._job
    debouncer.function = two_function

    # Call and let timer run out
    await debouncer.async_call()
    expect(len(calls)).to_equal(2)
    expect(calls).to_equal([1, 2])
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
    expect(calls).to_equal([1, 2])
    expect(debouncer._timer_task).to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(False)
    expect(debouncer._job.target).to_equal(debouncer.function)
    expect(debouncer._job != before_job).to_be(True)

    # Test calling enabled timer if currently executing.
    await debouncer._execute_lock.acquire()
    await debouncer.async_call()
    expect(len(calls)).to_equal(2)
    expect(calls).to_equal([1, 2])
    expect(debouncer._timer_task).not_.to_be_none()
    expect(debouncer._execute_at_end_of_timer).to_be(True)
    debouncer._execute_lock.release()
    expect(debouncer._job.target).to_equal(debouncer.function)

    debouncer.async_shutdown()


@test
async def shutdown(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test shutdown."""
    calls: list[Any] = []
    future: asyncio.Future[bool] = asyncio.Future()

    async def _func() -> None:
        await future
        calls.append(None)

    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=False,
        function=_func,
    )

    # Ensure shutdown during a run doesn't create a cooldown timer
    hass.async_create_task(debouncer.async_call())
    await asyncio.sleep(0.01)
    debouncer.async_shutdown()
    future.set_result(True)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).to_be_none()

    expect(
        "Debouncer call ignored as shutdown has been requested." not in caplog.text
    ).to_be(True)
    await debouncer.async_call()
    expect(
        "Debouncer call ignored as shutdown has been requested." in caplog.text
    ).to_be(True)

    expect(len(calls)).to_equal(1)
    expect(debouncer._timer_task).to_be_none()


@test
async def background(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test background tasks are created when background is True."""
    calls: list[Any] = []

    async def _func() -> None:
        await asyncio.sleep(0.1)
        calls.append(None)

    debouncer = debounce.Debouncer(
        hass, _LOGGER, cooldown=0.05, immediate=True, function=_func, background=True
    )

    await debouncer.async_call()
    expect(len(calls)).to_equal(1)

    debouncer.async_schedule_call()
    expect(len(calls)).to_equal(1)

    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done(wait_background_tasks=False)
    expect(len(calls)).to_equal(1)

    await hass.async_block_till_done(wait_background_tasks=True)
    expect(len(calls)).to_equal(2)

    async_fire_time_changed(hass, utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done(wait_background_tasks=False)
    expect(len(calls)).to_equal(2)


@test
async def shutdown_releases_parent_class(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test shutdown releases parent class.

    See https://github.com/home-assistant/core/issues/137237
    """
    calls: list[Any] = []

    class SomeClass:
        def run_func(self) -> None:
            calls.append(None)

    my_class = SomeClass()
    my_class_weak_ref = weakref.ref(my_class)

    debouncer = debounce.Debouncer(
        hass,
        _LOGGER,
        cooldown=0.01,
        immediate=True,
        function=my_class.run_func,
    )

    # Debouncer keeps a reference to the function, prevening GC
    del my_class
    await debouncer.async_call()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(my_class_weak_ref()).not_.to_be_none()

    # Debouncer shutdown releases the class
    debouncer.async_shutdown()
    expect(my_class_weak_ref()).to_be_none()
