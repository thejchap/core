"""Test config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires mqtt_mock broker fixture")
async def mqtt_setup() -> None:
    """Test we can finish a config flow through MQTT with custom prefix."""


@test.skip("requires mqtt_mock broker fixture")
async def duplicate() -> None:
    """Test duplicate entry abort."""


@test.skip("requires mqtt_mock broker fixture")
async def mqtt_setup_incomplete_payload() -> None:
    """Test incomplete payload abort."""


@test.skip("requires mqtt_mock broker fixture")
async def mqtt_setup_bad_json() -> None:
    """Test bad JSON abort."""


@test.skip("requires mqtt_mock broker fixture")
async def mqtt_setup_bad_topic() -> None:
    """Test bad topic abort."""


@test.skip("requires mqtt_mock broker fixture")
async def mqtt_setup_no_payload() -> None:
    """Test no payload abort."""


@test
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user setup."""
    result = await hass.config_entries.flow.async_init(
        "drop_connect", context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_supported")
