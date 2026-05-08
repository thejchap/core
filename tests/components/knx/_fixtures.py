"""Tryke fixtures for the knx integration."""

from collections.abc import AsyncGenerator
from typing import Any

from tryke import Depends, fixture
from xknx.io import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT

from homeassistant.components.knx.const import (
    CONF_KNX_AUTOMATIC,
    CONF_KNX_CONNECTION_TYPE,
    CONF_KNX_DEFAULT_RATE_LIMIT,
    CONF_KNX_DEFAULT_STATE_UPDATER,
    CONF_KNX_INDIVIDUAL_ADDRESS,
    CONF_KNX_MCAST_GRP,
    CONF_KNX_MCAST_PORT,
    CONF_KNX_RATE_LIMIT,
    CONF_KNX_STATE_UPDATER,
    DEFAULT_ROUTING_IA,
    DOMAIN,
)
from homeassistant.core import HomeAssistant

from .conftest import KNXTestKit

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx, hass_storage as hass_storage_fx


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="KNX",
        domain=DOMAIN,
        data={
            CONF_KNX_CONNECTION_TYPE: CONF_KNX_AUTOMATIC,
            CONF_KNX_RATE_LIMIT: CONF_KNX_DEFAULT_RATE_LIMIT,
            CONF_KNX_STATE_UPDATER: CONF_KNX_DEFAULT_STATE_UPDATER,
            CONF_KNX_MCAST_PORT: DEFAULT_MCAST_PORT,
            CONF_KNX_MCAST_GRP: DEFAULT_MCAST_GRP,
            CONF_KNX_INDIVIDUAL_ADDRESS: DEFAULT_ROUTING_IA,
        },
    )


@fixture
async def knx(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> AsyncGenerator[KNXTestKit]:
    """Create a KNX TestKit instance."""
    knx_test_kit = KNXTestKit(hass, mock_config_entry, hass_storage)
    yield knx_test_kit
    await knx_test_kit.assert_no_telegram()
