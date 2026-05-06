"""Test starting HA helpers."""

from tryke import Depends, expect, fixture, test

from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant, callback
from homeassistant.helpers import start

from tests.hass_fixtures import LogCapture, caplog, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def at_start_when_running_awaitable(hass: HomeAssistant = Depends(hass)) -> None:
    """Test at start when already running."""
    expect(hass.state is CoreState.running).to_be(True)
    expect(hass.is_running).to_be(True)

    calls = []

    async def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_start(hass, cb_at_start)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    hass.set_state(CoreState.starting)
    expect(hass.is_running).to_be(True)

    start.async_at_start(hass, cb_at_start)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)


@test
async def at_start_when_running_callback(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test at start when already running."""
    expect(hass.state is CoreState.running).to_be(True)
    expect(hass.is_running).to_be(True)

    calls = []

    @callback
    def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_start(hass, cb_at_start)()
    expect(len(calls)).to_equal(1)

    hass.set_state(CoreState.starting)
    expect(hass.is_running).to_be(True)

    start.async_at_start(hass, cb_at_start)()
    expect(len(calls)).to_equal(2)

    for record in caplog.records:
        expect(record.levelname in ("DEBUG", "INFO")).to_be(True)


@test
async def at_start_when_starting_awaitable(hass: HomeAssistant = Depends(hass)) -> None:
    """Test at start when yet to start."""
    hass.set_state(CoreState.not_running)
    expect(hass.is_running).to_be(False)

    calls = []

    async def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_start(hass, cb_at_start)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)


@test
async def at_start_when_starting_callback(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test at start when yet to start."""
    hass.set_state(CoreState.not_running)
    expect(hass.is_running).to_be(False)

    calls = []

    @callback
    def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    cancel = start.async_at_start(hass, cb_at_start)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    cancel()

    for record in caplog.records:
        expect(record.levelname in ("DEBUG", "INFO")).to_be(True)


@test
async def cancelling_at_start_when_running(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test cancelling at start when already running."""
    expect(hass.state is CoreState.running).to_be(True)
    expect(hass.is_running).to_be(True)

    calls = []

    async def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_start(hass, cb_at_start)()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    for record in caplog.records:
        expect(record.levelname in ("DEBUG", "INFO")).to_be(True)


@test
async def cancelling_at_start_when_starting(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test cancelling at start when yet to start."""
    hass.set_state(CoreState.not_running)
    expect(hass.is_running).to_be(False)

    calls = []

    @callback
    def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_start(hass, cb_at_start)()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)


@test
async def at_started_when_running_awaitable(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test at started when already started."""
    expect(hass.state is CoreState.running).to_be(True)

    calls = []

    async def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_started(hass, cb_at_start)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    hass.set_state(CoreState.starting)

    start.async_at_started(hass, cb_at_start)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)


@test
async def at_started_when_running_callback(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test at started when already running."""
    expect(hass.state is CoreState.running).to_be(True)

    calls = []

    @callback
    def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_started(hass, cb_at_start)()
    expect(len(calls)).to_equal(1)

    hass.set_state(CoreState.starting)

    start.async_at_started(hass, cb_at_start)()
    expect(len(calls)).to_equal(1)

    for record in caplog.records:
        expect(record.levelname in ("DEBUG", "INFO")).to_be(True)


@test
async def at_started_when_starting_awaitable(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test at started when yet to start."""
    hass.set_state(CoreState.not_running)

    calls = []

    async def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_started(hass, cb_at_start)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)


@test
async def at_started_when_starting_callback(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test at started when yet to start."""
    hass.set_state(CoreState.not_running)

    calls = []

    @callback
    def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    cancel = start.async_at_started(hass, cb_at_start)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    cancel()

    for record in caplog.records:
        expect(record.levelname in ("DEBUG", "INFO")).to_be(True)


@test
async def cancelling_at_started_when_running(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test cancelling at start when already running."""
    expect(hass.state is CoreState.running).to_be(True)
    expect(hass.is_running).to_be(True)

    calls = []

    async def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_started(hass, cb_at_start)()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    for record in caplog.records:
        expect(record.levelname in ("DEBUG", "INFO")).to_be(True)


@test
async def cancelling_at_started_when_starting(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test cancelling at start when yet to start."""
    hass.set_state(CoreState.not_running)
    expect(hass.is_running).to_be(False)

    calls = []

    @callback
    def cb_at_start(hass: HomeAssistant) -> None:
        """Home Assistant is started."""
        calls.append(1)

    start.async_at_started(hass, cb_at_start)()
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)
