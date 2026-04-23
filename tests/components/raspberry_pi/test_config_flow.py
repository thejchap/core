"""Test the Raspberry Pi config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.raspberry_pi.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry, MockModule, mock_integration
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def config_flow(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the config flow."""
    mock_integration(hass, MockModule("hassio"))

    with patch(
        "homeassistant.components.raspberry_pi.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "system"}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Raspberry Pi")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal({})
    expect(config_entry.title).to_equal("Raspberry Pi")


@test
async def config_flow_single_entry(hass: HomeAssistant = Depends(hass)) -> None:
    """Test only a single entry is allowed."""
    mock_integration(hass, MockModule("hassio"))

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={},
        title="Raspberry Pi",
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.raspberry_pi.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "system"}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
    mock_setup_entry.assert_not_called()
