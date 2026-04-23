"""Test emulated_roku component setup process."""

from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import emulated_roku
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def config_required_fields(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that configuration is successful with required fields."""
    with (
        patch.object(emulated_roku, "configured_servers", return_value=[]),
        patch(
            "homeassistant.components.emulated_roku.binding.EmulatedRokuServer",
            return_value=Mock(start=AsyncMock(), close=AsyncMock()),
        ),
    ):
        result = await async_setup_component(
            hass,
            emulated_roku.DOMAIN,
            {
                emulated_roku.DOMAIN: {
                    emulated_roku.CONF_SERVERS: [
                        {
                            emulated_roku.CONF_NAME: "Emulated Roku Test",
                            emulated_roku.CONF_LISTEN_PORT: 8060,
                        }
                    ]
                }
            },
        )
        expect(result).to_be(True)


@test
async def config_already_registered_not_configured(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that an already registered name causes the entry to be ignored."""
    with (
        patch(
            "homeassistant.components.emulated_roku.binding.EmulatedRokuServer",
            return_value=Mock(start=AsyncMock(), close=AsyncMock()),
        ) as instantiate,
        patch.object(
            emulated_roku, "configured_servers", return_value=["Emulated Roku Test"]
        ),
    ):
        result = await async_setup_component(
            hass,
            emulated_roku.DOMAIN,
            {
                emulated_roku.DOMAIN: {
                    emulated_roku.CONF_SERVERS: [
                        {
                            emulated_roku.CONF_NAME: "Emulated Roku Test",
                            emulated_roku.CONF_LISTEN_PORT: 8060,
                        }
                    ]
                }
            },
        )
        expect(result).to_be(True)

    expect(len(instantiate.mock_calls)).to_equal(0)


@test
async def setup_entry_successful(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup entry is successful."""
    entry = Mock()
    entry.data = {
        emulated_roku.CONF_NAME: "Emulated Roku Test",
        emulated_roku.CONF_LISTEN_PORT: 8060,
        emulated_roku.CONF_HOST_IP: "1.2.3.5",
        emulated_roku.CONF_ADVERTISE_IP: "1.2.3.4",
        emulated_roku.CONF_ADVERTISE_PORT: 8071,
        emulated_roku.CONF_UPNP_BIND_MULTICAST: False,
    }

    with patch(
        "homeassistant.components.emulated_roku.binding.EmulatedRokuServer",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ) as instantiate:
        result = await emulated_roku.async_setup_entry(hass, entry)
        expect(result).to_be(True)

    expect(len(instantiate.mock_calls)).to_equal(1)


@test
async def unload_entry(hass: HomeAssistant = Depends(hass)) -> None:
    """Test being able to unload an entry."""
    entry = Mock()
    entry.data = {
        "name": "Emulated Roku Test",
        "listen_port": 8060,
        emulated_roku.CONF_HOST_IP: "1.2.3.5",
    }

    with patch(
        "homeassistant.components.emulated_roku.binding.EmulatedRokuServer",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        result = await emulated_roku.async_setup_entry(hass, entry)
        expect(result).to_be(True)

    await hass.async_block_till_done()

    result = await emulated_roku.async_unload_entry(hass, entry)
    expect(bool(result)).to_be(True)
