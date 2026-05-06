"""Tests for the Sun config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.sun.const import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_user_flow(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    with patch(
        "homeassistant.components.sun.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("Sun")
    expect(result.get("data")).to_equal({})
    expect(result.get("options")).to_equal({})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("user_source", source=SOURCE_USER),
    test.case("import_source", source=SOURCE_IMPORT),
)
async def single_instance_allowed(
    source: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test we abort if already setup."""
    mock_config_entry = MockConfigEntry(domain=DOMAIN)

    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": source}
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("single_instance_allowed")


@test
async def import_flow(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the import configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("Sun")
    expect(result.get("data")).to_equal({})
    expect(result.get("options")).to_equal({})
