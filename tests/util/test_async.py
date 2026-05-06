"""Tests for async util methods from Python source."""

import asyncio
import re
import time
from unittest.mock import MagicMock, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.util import async_ as hasync

from tests.common import extract_stack_to_frame
from tests.hass_fixtures import LogCapture, caplog, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported `hass` resolves via Depends()."""
    return 0


@test
@patch("concurrent.futures.Future")
@patch("threading.get_ident")
def run_callback_threadsafe_from_inside_event_loop(
    mock_ident: MagicMock, mock_future: MagicMock
) -> None:
    """Testing calling run_callback_threadsafe from inside an event loop."""
    callback = MagicMock()

    loop = Mock(spec=["call_soon_threadsafe"])

    loop._thread_id = None
    mock_ident.return_value = 5
    hasync.run_callback_threadsafe(loop, callback)
    expect(len(loop.call_soon_threadsafe.mock_calls)).to_equal(1)

    loop._thread_id = 5
    mock_ident.return_value = 5
    expect(lambda: hasync.run_callback_threadsafe(loop, callback)).to_raise(
        RuntimeError
    )
    expect(len(loop.call_soon_threadsafe.mock_calls)).to_equal(1)

    loop._thread_id = 1
    mock_ident.return_value = 5
    hasync.run_callback_threadsafe(loop, callback)
    expect(len(loop.call_soon_threadsafe.mock_calls)).to_equal(2)


@test
async def gather_with_limited_concurrency() -> None:
    """Test gather_with_limited_concurrency limits the number of running tasks."""

    runs = 0
    now_time = time.time()

    async def _increment_runs_if_in_time() -> int:
        if time.time() - now_time > 0.1:
            return -1

        nonlocal runs
        runs += 1
        await asyncio.sleep(0.1)
        return runs

    results = await hasync.gather_with_limited_concurrency(
        2, *(_increment_runs_if_in_time() for i in range(4))
    )

    expect(results).to_equal([2, 2, -1, -1])


@test
async def shutdown_run_callback_threadsafe(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test we can shutdown run_callback_threadsafe."""
    hasync.shutdown_run_callback_threadsafe(hass.loop)
    callback = MagicMock()

    expect(lambda: hasync.run_callback_threadsafe(hass.loop, callback)).to_raise(
        RuntimeError
    )


@test
async def run_callback_threadsafe(hass: HomeAssistant = Depends(hass)) -> None:
    """Test run_callback_threadsafe runs code in the event loop."""
    it_ran = False

    def callback() -> None:
        nonlocal it_ran
        it_ran = True

    with patch.dict(hass.loop.__dict__, {"_thread_id": -1}):
        expect(hasync.run_callback_threadsafe(hass.loop, callback)).to_be_truthy()
    expect(it_ran).to_be(False)

    # Verify that async_block_till_done will flush out the callback.
    await hass.async_block_till_done()
    expect(it_ran).to_be(True)


@test
async def callback_is_always_scheduled(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test run_callback_threadsafe always calls call_soon_threadsafe before checking for shutdown."""
    # We have to check the shutdown state AFTER the callback is scheduled
    # otherwise the function could continue on and the caller call
    # `future.result()` after the point in the main thread where
    # callbacks are no longer run.

    callback = MagicMock()
    hasync.shutdown_run_callback_threadsafe(hass.loop)

    with (
        patch.dict(hass.loop.__dict__, {"_thread_id": -1}),
        patch.object(hass.loop, "call_soon_threadsafe") as mock_call_soon_threadsafe,
    ):
        expect(lambda: hasync.run_callback_threadsafe(hass.loop, callback)).to_raise(
            RuntimeError
        )

    mock_call_soon_threadsafe.assert_called_once()


@test
async def create_eager_task_312(hass: HomeAssistant = Depends(hass)) -> None:
    """Test create_eager_task schedules a task eagerly in the event loop.

    For Python 3.12+, the task is scheduled eagerly in the event loop.
    """
    events: list[str] = []

    async def _normal_task() -> None:
        events.append("normal")

    async def _eager_task() -> None:
        events.append("eager")

    task1 = hasync.create_eager_task(_eager_task())
    task2 = asyncio.create_task(_normal_task())

    expect(events).to_equal(["eager"])

    await asyncio.sleep(0)
    expect(events).to_equal(["eager", "normal"])
    await task1
    await task2


@test
async def create_eager_task_from_thread(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test we report trying to create an eager task from a thread."""

    coro = asyncio.sleep(0)

    def create_task() -> None:
        hasync.create_eager_task(coro)

    raised: BaseException | None = None
    try:
        await hass.async_add_executor_job(create_task)
    except RuntimeError as exc:
        raised = exc
    expect(raised).not_.to_be(None)
    assert raised is not None
    expect(
        bool(
            re.search(
                "Detected code that attempted to create an asyncio task "
                "from a thread. Please report this issue",
                str(raised),
            )
        )
    ).to_be(True)

    # Avoid `RuntimeWarning: coroutine 'sleep' was never awaited`.
    await coro


@test
async def create_eager_task_from_thread_in_integration(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test we report trying to create an eager task from a thread."""

    coro = asyncio.sleep(0)

    def create_task() -> None:
        hasync.create_eager_task(coro)

    frames = extract_stack_to_frame(
        [
            Mock(
                filename="/home/paulus/homeassistant/core.py",
                lineno="23",
                line="do_something()",
            ),
            Mock(
                filename="/home/paulus/homeassistant/components/hue/light.py",
                lineno="23",
                line="self.light.is_on",
            ),
            Mock(
                filename="/home/paulus/aiohue/lights.py",
                lineno="2",
                line="something()",
            ),
        ]
    )
    with (
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value="self.light.is_on",
        ),
        patch(
            "homeassistant.util.loop._get_line_from_cache",
            return_value="mock_line",
        ),
        patch(
            "homeassistant.util.loop.get_current_frame",
            return_value=frames,
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=frames,
        ),
    ):
        raised: BaseException | None = None
        try:
            await hass.async_add_executor_job(create_task)
        except RuntimeError as exc:
            raised = exc
        expect(raised).not_.to_be(None)
        assert raised is not None
        expect("no running event loop" in str(raised)).to_be(True)

    expect(
        "Detected that integration 'hue' attempted to create an asyncio task "
        "from a thread at homeassistant/components/hue/light.py, line 23: "
        "self.light.is_on" in caplog.text
    ).to_be(True)

    # Avoid `RuntimeWarning: coroutine 'sleep' was never awaited`.
    await coro


@test
async def get_scheduled_timer_handles(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test get_scheduled_timer_handles returns all scheduled timer handles."""
    loop = hass.loop
    timer_handle = loop.call_later(10, lambda: None)
    timer_handle2 = loop.call_later(5, lambda: None)
    timer_handle3 = loop.call_later(15, lambda: None)

    handles = hasync.get_scheduled_timer_handles(loop)
    expect(set(handles).issuperset({timer_handle, timer_handle2, timer_handle3})).to_be(
        True
    )
    timer_handle.cancel()
    timer_handle2.cancel()
    timer_handle3.cancel()
