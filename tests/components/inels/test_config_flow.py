"""Test the iNELS config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.inels.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires mqtt_mock fixture (not yet in shim)")
async def mqtt_config_single_instance(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """The MQTT test flow is aborted if an entry already exists."""


@test.skip("requires mqtt_mock fixture (not yet in shim)")
async def mqtt_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """When an MQTT message is received on the discovery topic, it triggers a config flow."""


@test.skip("requires mqtt_mock fixture (not yet in shim)")
async def mqtt_abort_invalid_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check MQTT flow aborts if discovery topic is invalid."""


@test.skip("requires mqtt_mock fixture (not yet in shim)")
async def mqtt_abort_empty_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check MQTT flow aborts if discovery payload is empty."""


@test.skip("requires mqtt_mock fixture (not yet in shim)")
async def mqtt_abort_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that a second MQTT flow is aborted when one is already in progress."""


@test.skip("requires mqtt_mock fixture (not yet in shim)")
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if the user can finish a config flow."""


@test.skip("requires mqtt_mock fixture (not yet in shim)")
async def user_config_single_instance(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """The user test flow is aborted if an entry already exists."""


@test.skip("requires mqtt_mock fixture (not yet in shim)")
async def user_setup_mqtt_not_connected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """The user setup test flow is aborted when MQTT is not connected."""


@test
async def user_setup_mqtt_not_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """The user setup test flow is aborted when MQTT is not configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("mqtt_not_configured")
