"""Test Home Assistant thread utils."""

import asyncio
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.util import thread
from homeassistant.util.async_ import run_callback_threadsafe
from homeassistant.util.thread import ThreadWithException

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported `hass` resolves via Depends()."""
    return 0


class _EmptyClass:
    """An empty class."""


@test
async def thread_with_exception_invalid(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test throwing an invalid thread exception."""
    finish_event = asyncio.Event()

    def _do_nothing(*_: object) -> None:
        run_callback_threadsafe(hass.loop, finish_event.set)

    test_thread = ThreadWithException(target=_do_nothing)
    test_thread.start()
    await asyncio.wait_for(finish_event.wait(), timeout=0.1)

    expect(lambda: test_thread.raise_exc(_EmptyClass())).to_raise(TypeError)
    test_thread.join()


@test
async def thread_not_started() -> None:
    """Test throwing when the thread is not started."""
    test_thread = ThreadWithException(target=lambda *_: None)

    expect(lambda: test_thread.raise_exc(TimeoutError)).to_raise(AssertionError)


@test
async def thread_fails_raise(hass: HomeAssistant = Depends(hass)) -> None:
    """Test throwing after already ended."""
    finish_event = asyncio.Event()

    def _do_nothing(*_: object) -> None:
        run_callback_threadsafe(hass.loop, finish_event.set)

    test_thread = ThreadWithException(target=_do_nothing)
    test_thread.start()
    await asyncio.wait_for(finish_event.wait(), timeout=0.1)
    test_thread.join()

    expect(lambda: test_thread.raise_exc(ValueError)).to_raise(SystemError)


@test
async def deadlock_safe_shutdown_no_threads() -> None:
    """Test we can shutdown without deadlock without any threads to join."""
    dead_thread_mock = Mock(
        join=Mock(), daemon=False, is_alive=Mock(return_value=False)
    )
    daemon_thread_mock = Mock(
        join=Mock(), daemon=True, is_alive=Mock(return_value=True)
    )
    mock_threads = [dead_thread_mock, daemon_thread_mock]

    with patch("homeassistant.util.threading.enumerate", return_value=mock_threads):
        thread.deadlock_safe_shutdown()

    expect(dead_thread_mock.join.called).to_be(False)
    expect(daemon_thread_mock.join.called).to_be(False)


@test
async def deadlock_safe_shutdown() -> None:
    """Test we can shutdown without deadlock."""
    normal_thread_mock = Mock(
        join=Mock(), daemon=False, is_alive=Mock(return_value=True)
    )
    dead_thread_mock = Mock(
        join=Mock(), daemon=False, is_alive=Mock(return_value=False)
    )
    daemon_thread_mock = Mock(
        join=Mock(), daemon=True, is_alive=Mock(return_value=True)
    )
    exception_thread_mock = Mock(
        join=Mock(side_effect=Exception),
        daemon=False,
        is_alive=Mock(return_value=True),
    )
    mock_threads = [
        normal_thread_mock,
        dead_thread_mock,
        daemon_thread_mock,
        exception_thread_mock,
    ]

    with patch("homeassistant.util.threading.enumerate", return_value=mock_threads):
        thread.deadlock_safe_shutdown()

    expected_timeout = thread.THREADING_SHUTDOWN_TIMEOUT / 2

    expect(normal_thread_mock.join.call_args[0]).to_equal((expected_timeout,))
    expect(dead_thread_mock.join.called).to_be(False)
    expect(daemon_thread_mock.join.called).to_be(False)
    expect(exception_thread_mock.join.call_args[0]).to_equal((expected_timeout,))
