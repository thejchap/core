"""The tests for the Roku remote platform."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.remote import (
    ATTR_COMMAND,
    DOMAIN as REMOTE_DOMAIN,
    SERVICE_SEND_COMMAND,
)
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import UPNP_SERIAL
from ._fixtures import init_integration, mock_roku

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

MAIN_ENTITY_ID = f"{REMOTE_DOMAIN}.my_roku_3"


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test setup with basic config."""
    expect(hass.states.get(MAIN_ENTITY_ID) is not None).to_be(True)


@test
async def unique_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    init_integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test unique id."""
    main = entity_registry.async_get(MAIN_ENTITY_ID)
    expect(main.unique_id).to_equal(UPNP_SERIAL)


@test
async def main_services(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration),
    mock_roku: MagicMock = Depends(mock_roku),
) -> None:
    """Test platform services."""
    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID},
        blocking=True,
    )
    expect(mock_roku.remote.call_count).to_equal(1)
    mock_roku.remote.assert_called_with("poweroff")

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID},
        blocking=True,
    )
    expect(mock_roku.remote.call_count).to_equal(2)
    mock_roku.remote.assert_called_with("poweron")

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: MAIN_ENTITY_ID, ATTR_COMMAND: ["home"]},
        blocking=True,
    )
    expect(mock_roku.remote.call_count).to_equal(3)
    mock_roku.remote.assert_called_with("home")
