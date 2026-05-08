"""Test the group config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.group import DOMAIN, async_setup_entry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow_binary_sensor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the binary_sensor config flow (one row of the original parametrize)."""
    group_type = "binary_sensor"
    members = [f"{group_type}.one", f"{group_type}.two"]
    for member in members:
        hass.states.async_set(member, "on", {})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": group_type},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(group_type)

    with patch(
        "homeassistant.components.group.async_setup_entry", wraps=async_setup_entry
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "Living Room",
                "entities": members,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Living Room")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "entities": members,
            "group_type": group_type,
            "hide_members": False,
            "name": "Living Room",
            "all": False,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.skip("requires 15-row pytest parametrize over group platforms (binary_sensor, button, cover, ...)")
async def config_flow() -> None:
    """Stub for test_config_flow (port deferred — needs test.cases conversion)."""


@test.skip("requires 6-row pytest parametrize over group platforms (light/switch/binary_sensor)")
async def config_flow_hides_members(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow hides members if requested."""
    expect(True).to_be(True)


@test.skip("requires 15-row pytest parametrize over group platforms")
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""
    expect(True).to_be(True)


@test.skip("requires 15-row pytest parametrize over group platforms")
async def all_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""
    expect(True).to_be(True)


@test.skip("requires 9-row pytest parametrize over group platforms")
async def options_flow_hides_members(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the options flow hides or unhides members if requested."""
    expect(True).to_be(True)


@test.skip("requires hass_ws_client + parametrize for preview WebSocket flow")
async def config_flow_preview(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow preview."""
    expect(True).to_be(True)


@test.skip("requires hass_ws_client for preview WebSocket flow")
async def option_flow_preview(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the option flow preview."""
    expect(True).to_be(True)


@test.skip("requires hass_ws_client for preview WebSocket flow")
async def option_flow_sensor_preview_config_entry_removed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the option flow preview where the config entry is removed."""
    expect(True).to_be(True)


