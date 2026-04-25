"""Test the Demo config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, setup
from homeassistant.components.demo import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import disable_platforms, setup_homeassistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(setup_homeassistant),
    _disable_platforms: None = Depends(disable_platforms),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def import_(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we can import a config entry."""
    with patch("homeassistant.components.demo.async_setup_entry", return_value=True):
        expect(await setup.async_setup_component(hass, DOMAIN, {DOMAIN: {}})).to_be(
            True
        )
        await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.data).to_equal({})


@test
async def import_once(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we don't create multiple config entries."""
    with patch(
        "homeassistant.components.demo.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={},
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Demo")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({})
    mock_setup_entry.assert_called_once()

    # Test importing again doesn't create a 2nd entry
    with patch("homeassistant.components.demo.async_setup_entry") as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
    mock_setup_entry.assert_not_called()


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("options_1")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"bool": True, "constant": "Constant Value", "int": 15},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("options_2")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            "bool": True,
            "constant": "Constant Value",
            "int": 15,
            "multi": ["default"],
            "select": "default",
            "string": "Default",
        }
    )

    await hass.async_block_till_done()
    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
