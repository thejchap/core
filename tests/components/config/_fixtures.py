"""Tryke fixtures for the config integration auth tests."""

from __future__ import annotations

from typing import Any

from tryke import Depends, fixture

from homeassistant.components.config import area_registry as area_registry_config
from homeassistant.components.config import auth as auth_config
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant

from tests.common import CLIENT_ID
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_read_only_user as hass_read_only_user_fx,
    hass_ws_client as hass_ws_client_fx,
    local_auth as local_auth_fx,
)


@fixture
async def setup_config(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Set up the auth provider homeassistant module on the hass instance."""
    auth_config.async_setup(hass)
    return hass


@fixture
async def hass_read_only_access_token(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_read_only_user: Any = Depends(hass_read_only_user_fx),
    _local_auth: Any = Depends(local_auth_fx),
) -> str:
    """Return an access token for the read-only user."""
    from homeassistant.auth.models import Credentials  # noqa: PLC0415

    credential = Credentials(
        id="mock-readonly-credential-id",
        auth_provider_type="homeassistant",
        auth_provider_id=None,
        data={"username": "readonly"},
        is_new=False,
    )
    hass_read_only_user.credentials.append(credential)

    refresh_token = await hass.auth.async_create_refresh_token(
        hass_read_only_user, CLIENT_ID, credential=credential
    )
    return hass.auth.async_create_access_token(refresh_token)


@fixture
async def area_registry_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> Any:
    """WebSocket client wired to the area_registry config module."""
    area_registry_config.async_setup(hass)
    return await hass_ws_client(hass)


@fixture
async def mock_temperature_humidity_entity(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Mock temperature and humidity sensors."""
    hass.states.async_set(
        "sensor.mock_temperature",
        "20",
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        },
    )
    hass.states.async_set(
        "sensor.mock_humidity",
        "50",
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
            ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
        },
    )
