"""Test dispatcher helpers."""

from functools import partial
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.util.signal_type import SignalType, SignalTypeFormat

from tests.hass_fixtures import LogCapture, caplog, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def simple_function(hass: HomeAssistant = Depends(hass)) -> None:
    """Test simple function (executor)."""
    calls: list[Any] = []

    def test_funct(data: Any) -> None:
        """Test function."""
        calls.append(data)

    async_dispatcher_connect(hass, "test", test_funct)
    async_dispatcher_send(hass, "test", 3)
    await hass.async_block_till_done()

    expect(calls).to_equal([3])

    async_dispatcher_send(hass, "test", "bla")
    await hass.async_block_till_done()

    expect(calls).to_equal([3, "bla"])


@test
async def signal_type(hass: HomeAssistant = Depends(hass)) -> None:
    """Test dispatcher with SignalType."""
    signal: SignalType[str, int] = SignalType("test")
    calls: list[tuple[str, int]] = []

    def test_funct(data1: str, data2: int) -> None:
        calls.append((data1, data2))

    async_dispatcher_connect(hass, signal, test_funct)
    async_dispatcher_send(hass, signal, "Hello", 2)
    await hass.async_block_till_done()

    expect(calls).to_equal([("Hello", 2)])

    async_dispatcher_send(hass, signal, "World", 3)
    await hass.async_block_till_done()

    expect(calls).to_equal([("Hello", 2), ("World", 3)])

    # Test compatibility with string keys
    async_dispatcher_send(hass, "test", "x", 4)
    await hass.async_block_till_done()

    expect(calls).to_equal([("Hello", 2), ("World", 3), ("x", 4)])


@test
async def signal_type_format(hass: HomeAssistant = Depends(hass)) -> None:
    """Test dispatcher with SignalType and format."""
    signal: SignalTypeFormat[str, int] = SignalTypeFormat("test-{}")
    calls: list[tuple[str, int]] = []

    def test_funct(data1: str, data2: int) -> None:
        calls.append((data1, data2))

    async_dispatcher_connect(hass, signal.format("unique-id"), test_funct)
    async_dispatcher_send(hass, signal.format("unique-id"), "Hello", 2)
    await hass.async_block_till_done()

    expect(calls).to_equal([("Hello", 2)])

    # Test compatibility with string keys
    async_dispatcher_send(hass, "test-unique-id", "x", 4)
    await hass.async_block_till_done()

    expect(calls).to_equal([("Hello", 2), ("x", 4)])


@test
async def simple_function_unsub(hass: HomeAssistant = Depends(hass)) -> None:
    """Test simple function (executor) and unsub."""
    calls1: list[Any] = []
    calls2: list[Any] = []

    def test_funct1(data: Any) -> None:
        """Test function."""
        calls1.append(data)

    def test_funct2(data: Any) -> None:
        """Test function."""
        calls2.append(data)

    async_dispatcher_connect(hass, "test1", test_funct1)
    unsub = async_dispatcher_connect(hass, "test2", test_funct2)
    async_dispatcher_send(hass, "test1", 3)
    async_dispatcher_send(hass, "test2", 4)
    await hass.async_block_till_done()

    expect(calls1).to_equal([3])
    expect(calls2).to_equal([4])

    unsub()

    async_dispatcher_send(hass, "test1", 5)
    async_dispatcher_send(hass, "test2", 6)
    await hass.async_block_till_done()

    expect(calls1).to_equal([3, 5])
    expect(calls2).to_equal([4])

    # check don't kill the flow
    unsub()

    async_dispatcher_send(hass, "test1", 7)
    async_dispatcher_send(hass, "test2", 8)
    await hass.async_block_till_done()

    expect(calls1).to_equal([3, 5, 7])
    expect(calls2).to_equal([4])


@test
async def simple_callback(hass: HomeAssistant = Depends(hass)) -> None:
    """Test simple callback (async)."""
    calls: list[Any] = []

    @callback
    def test_funct(data: Any) -> None:
        """Test function."""
        calls.append(data)

    async_dispatcher_connect(hass, "test", test_funct)
    async_dispatcher_send(hass, "test", 3)
    await hass.async_block_till_done()

    expect(calls).to_equal([3])

    async_dispatcher_send(hass, "test", "bla")
    await hass.async_block_till_done()

    expect(calls).to_equal([3, "bla"])


@test
async def simple_coro(hass: HomeAssistant = Depends(hass)) -> None:
    """Test simple coro (async)."""
    calls: list[Any] = []

    async def async_test_funct(data: Any) -> None:
        """Test function."""
        calls.append(data)

    async_dispatcher_connect(hass, "test", async_test_funct)
    async_dispatcher_send(hass, "test", 3)
    await hass.async_block_till_done()

    expect(calls).to_equal([3])

    async_dispatcher_send(hass, "test", "bla")
    await hass.async_block_till_done()

    expect(calls).to_equal([3, "bla"])


@test
async def simple_function_multiargs(hass: HomeAssistant = Depends(hass)) -> None:
    """Test simple function (executor)."""
    calls: list[Any] = []

    def test_funct(data1: Any, data2: Any, data3: Any) -> None:
        """Test function."""
        calls.append(data1)
        calls.append(data2)
        calls.append(data3)

    async_dispatcher_connect(hass, "test", test_funct)
    async_dispatcher_send(hass, "test", 3, 2, "bla")
    await hass.async_block_till_done()

    expect(calls).to_equal([3, 2, "bla"])


@test
async def callback_exception_gets_logged(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test exception raised by signal handler."""

    @callback
    def bad_handler(*args: Any) -> None:
        """Record calls."""
        raise Exception("This is a bad message callback")  # noqa: TRY002

    # wrap in partial to test message logging.
    async_dispatcher_connect(hass, "test", partial(bad_handler))
    async_dispatcher_send(hass, "test", "bad")

    expect(
        f"Exception in functools.partial({bad_handler}) when dispatching 'test': ('bad',)"
        in caplog.text
    ).to_be(True)


@test
async def coro_exception_gets_logged(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test exception raised by signal handler."""

    async def bad_async_handler(*args: Any) -> None:
        """Record calls."""
        raise Exception("This is a bad message in a coro")  # noqa: TRY002

    # wrap in partial to test message logging.
    async_dispatcher_connect(hass, "test", bad_async_handler)
    async_dispatcher_send(hass, "test", "bad")
    await hass.async_block_till_done()

    expect("bad_async_handler" in caplog.text).to_be(True)
    expect("when dispatching 'test': ('bad',)" in caplog.text).to_be(True)


@test
async def dispatcher_add_dispatcher(hass: HomeAssistant = Depends(hass)) -> None:
    """Test adding a dispatcher from a dispatcher."""
    calls: list[Any] = []

    @callback
    def _new_dispatcher(data: Any) -> None:
        calls.append(data)

    @callback
    def _add_new_dispatcher(data: Any) -> None:
        calls.append(data)
        async_dispatcher_connect(hass, "test", _new_dispatcher)

    async_dispatcher_connect(hass, "test", _add_new_dispatcher)

    async_dispatcher_send(hass, "test", 3)
    async_dispatcher_send(hass, "test", 4)
    async_dispatcher_send(hass, "test", 5)

    expect(calls).to_equal([3, 4, 4, 5, 5])


@test
async def thread_safety_checks(hass: HomeAssistant = Depends(hass)) -> None:
    """Test dispatcher thread safety checks."""
    calls: list[Any] = []

    @callback
    def _dispatcher(data: Any) -> None:
        calls.append(data)

    async_dispatcher_connect(hass, "test", _dispatcher)

    caught: Exception | None = None
    try:
        await hass.async_add_executor_job(async_dispatcher_send, hass, "test", 3)
    except RuntimeError as exc:
        caught = exc
    expect(caught).not_.to_be_none()
    expect(
        "Detected code that calls async_dispatcher_send from a thread" in str(caught)
    ).to_be(True)

    async_dispatcher_send(hass, "test", 4)
    expect(calls).to_equal([4])
