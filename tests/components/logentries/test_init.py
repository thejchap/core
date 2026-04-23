"""The tests for the Logentries component."""

from collections.abc import Generator
from unittest.mock import ANY, MagicMock, call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import logentries
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def setup_config_full(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup with all data."""
    config = {"logentries": {"token": "secret"}}
    result = await async_setup_component(hass, logentries.DOMAIN, config)
    expect(result).to_be(True)

    with patch("homeassistant.components.logentries.requests.post") as mock_post:
        hass.states.async_set("fake.entity", STATE_ON)
        await hass.async_block_till_done()
        expect(len(mock_post.mock_calls)).to_equal(1)


@test
async def setup_config_defaults(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup with defaults."""
    config = {"logentries": {"token": "token"}}
    result = await async_setup_component(hass, logentries.DOMAIN, config)
    expect(result).to_be(True)

    with patch("homeassistant.components.logentries.requests.post") as mock_post:
        hass.states.async_set("fake.entity", STATE_ON)
        await hass.async_block_till_done()
        expect(len(mock_post.mock_calls)).to_equal(1)


@fixture
def mock_dump() -> Generator[MagicMock]:
    """Mock json dumps."""
    with patch("json.dumps") as mock_dump:
        yield mock_dump


@fixture
def mock_requests() -> Generator[MagicMock]:
    """Mock requests."""
    with patch.object(logentries, "requests") as mock_requests:
        yield mock_requests


@test
async def event_listener(
    hass: HomeAssistant = Depends(hass),
    mock_dump: MagicMock = Depends(mock_dump),
    mock_requests: MagicMock = Depends(mock_requests),
) -> None:
    """Test event listener."""
    mock_dump.side_effect = lambda x: x
    mock_post = mock_requests.post
    mock_requests.exceptions.RequestException = Exception
    config = {"logentries": {"token": "token"}}
    result = await async_setup_component(hass, logentries.DOMAIN, config)
    expect(result).to_be(True)

    valid = {"1": 1, "1.0": 1.0, STATE_ON: 1, STATE_OFF: 0, "foo": "foo"}
    for in_, out in valid.items():
        payload = {
            "host": "https://webhook.logentries.com/noformat/logs/token",
            "event": [
                {
                    "domain": "fake",
                    "entity_id": "entity",
                    "attributes": {},
                    "time": ANY,
                    "value": out,
                }
            ],
        }
        hass.states.async_set("fake.entity", in_)
        await hass.async_block_till_done()
        expect(mock_post.call_count).to_equal(1)
        expect(mock_post.call_args).to_equal(
            call(payload["host"], data=payload, timeout=10)
        )
        mock_post.reset_mock()
