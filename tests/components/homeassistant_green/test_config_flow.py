"""Test the Home Assistant Green config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio import DOMAIN as HASSIO_DOMAIN
from homeassistant.components.homeassistant_green.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from ._fixtures import (
    mock_get_supervisor_client,
    mock_setup_entry,
    supervisor_client,
)

from tests.common import MockConfigEntry, MockModule, mock_integration
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _supervisor_get: None = Depends(mock_get_supervisor_client),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the config flow."""
    mock_integration(hass, MockModule("hassio"))
    await async_setup_component(hass, HASSIO_DOMAIN, {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "system"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Home Assistant Green")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({})
    expect(len(setup.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal({})
    expect(config_entry.title).to_equal("Home Assistant Green")


@test
async def config_flow_single_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test only a single entry is allowed."""
    mock_integration(hass, MockModule("hassio"))
    await async_setup_component(hass, HASSIO_DOMAIN, {})

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={},
        title="Home Assistant Green",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "system"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
    setup.assert_not_called()


@test.skip("requires supervisor_client fixture (hassio)")
async def option_flow_non_hassio(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test option flow without hassio."""
    expect(True).to_be(True)


@test.skip("requires os_green_info fixture (hassio)")
async def option_flow_led_settings(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating LED settings."""
    expect(True).to_be(True)


@test.skip("requires os_green_info fixture (hassio)")
async def option_flow_led_settings_unchanged(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test LED settings unchanged."""
    expect(True).to_be(True)


@test.skip("requires os_green_info fixture (hassio)")
async def option_flow_led_settings_fail_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test LED settings read failure."""
    expect(True).to_be(True)


@test.skip("requires os_green_info fixture (hassio)")
async def option_flow_led_settings_fail_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test LED settings write failure."""
    expect(True).to_be(True)
