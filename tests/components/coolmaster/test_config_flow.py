"""Test the Coolmaster config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.coolmaster.config_flow import AVAILABLE_MODES
from homeassistant.components.coolmaster.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _flow_data(advanced: bool = False) -> dict[str, object]:
    options: dict[str, object] = {"host": "1.1.1.1"}
    for mode in AVAILABLE_MODES:
        options[mode] = True
    options["swing_support"] = False
    if advanced:
        options["send_wakeup_prompt"] = True
    return options


async def _form_base(hass: HomeAssistant, advanced: bool) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_USER,
            "show_advanced_options": advanced,
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.coolmaster.config_flow.CoolMasterNet.status",
            return_value={"test_id": "test_unit"},
        ),
        patch(
            "homeassistant.components.coolmaster.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], _flow_data(advanced)
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.1.1.1")
    _expected_data: dict[str, object] = {
        "host": "1.1.1.1",
        "port": 10102,
        "supported_modes": AVAILABLE_MODES,
        "swing_support": False,
        "send_wakeup_prompt": False,
    }
    if advanced:
        _expected_data["send_wakeup_prompt"] = True
    expect(result2["data"]).to_equal(_expected_data)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_non_advanced(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form in non-advanced mode."""
    await _form_base(hass, advanced=False)


@test
async def form_advanced(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form in advanced mode."""
    await _form_base(hass, advanced=True)


@test
async def form_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a connection timeout."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.coolmaster.config_flow.CoolMasterNet.status",
        side_effect=TimeoutError(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], _flow_data()
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_connection_refused(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.coolmaster.config_flow.CoolMasterNet.status",
        side_effect=ConnectionRefusedError(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], _flow_data()
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_no_units(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle no units found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.coolmaster.config_flow.CoolMasterNet.status",
        return_value={},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], _flow_data()
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "no_units"})
