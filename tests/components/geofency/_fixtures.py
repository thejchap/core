"""Tryke fixtures for geofency tests."""

from collections.abc import Generator
from unittest.mock import patch

from aiohttp.test_utils import TestClient
from tryke import Depends, fixture

from homeassistant import config_entries
from homeassistant.components import zone
from homeassistant.components.device_tracker.legacy import Device
from homeassistant.components.geofency import CONF_MOBILE_BEACONS, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client_no_auth,
)


@fixture
def mock_device_tracker_conf() -> Generator[list[Device]]:
    """Prevent device tracker from reading/writing data."""
    devices: list[Device] = []

    async def mock_update_config(path: str, dev_id: str, entity: Device) -> None:
        devices.append(entity)

    with (
        patch(
            (
                "homeassistant.components.device_tracker.legacy"
                ".DeviceTracker.async_update_config"
            ),
            side_effect=mock_update_config,
        ),
        patch(
            "homeassistant.components.device_tracker.legacy.async_load_config",
            side_effect=lambda *args: devices,
        ),
    ):
        yield devices


@fixture
async def setup_zones(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up Zone config in HA."""
    await async_setup_component(
        hass,
        zone.DOMAIN,
        {
            "zone": {
                "name": "Home",
                "latitude": 37.239622,
                "longitude": -115.815811,
                "radius": 100,
            }
        },
    )
    await hass.async_block_till_done()


@fixture
async def geofency_client(
    _mock_dev: list[Device] = Depends(mock_device_tracker_conf),
    _zones: None = Depends(setup_zones),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth_fx: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> TestClient:
    """Geofency mock client (unauthenticated)."""

    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {CONF_MOBILE_BEACONS: ["Car 1"]}}
    )
    await hass.async_block_till_done()

    with patch("homeassistant.components.device_tracker.legacy.update_config"):
        return await hass_client_no_auth_fx()


@fixture
async def webhook_id(
    hass: HomeAssistant = Depends(hass_fixture),
) -> str:
    """Initialize the Geofency component and get the webhook_id."""
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:8123"},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM, result

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()
    return result["result"].data["webhook_id"]
