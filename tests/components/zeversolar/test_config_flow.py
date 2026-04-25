"""Test the Zeversolar config flow."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test
from zeversolar.exceptions import (
    ZeverSolarHTTPError,
    ZeverSolarHTTPNotFound,
    ZeverSolarTimeout,
)

from homeassistant import config_entries
from homeassistant.components.zeversolar.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _set_up_zeversolar(hass: HomeAssistant, flow_id: str) -> None:
    """Reusable successful setup of Zeversolar sensor."""
    mock_data = MagicMock()
    mock_data.serial_number = "test_serial"
    with (
        patch("zeversolar.ZeverSolarClient.get_data", return_value=mock_data),
        patch(
            "homeassistant.components.zeversolar.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=flow_id,
            user_input={
                CONF_HOST: "test_ip",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Zeversolar")
    expect(result2["data"]).to_equal({CONF_HOST: "test_ip"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    await _set_up_zeversolar(hass=hass, flow_id=result["flow_id"])


@test.cases(
    test.case("not_found", side_effect=ZeverSolarHTTPNotFound, errors={"base": "invalid_host"}),
    test.case("http_error", side_effect=ZeverSolarHTTPError, errors={"base": "cannot_connect"}),
    test.case("timeout", side_effect=ZeverSolarTimeout, errors={"base": "timeout_connect"}),
    test.case("unknown", side_effect=RuntimeError, errors={"base": "unknown"}),
)
async def form_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    errors: dict,
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "zeversolar.ZeverSolarClient.get_data",
        side_effect=side_effect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input={
                CONF_HOST: "test_ip",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal(errors)

    await _set_up_zeversolar(hass=hass, flow_id=result["flow_id"])


@test
async def abort_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort when the device is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Zeversolar",
        data={CONF_HOST: "test_ip"},
        unique_id="test_serial",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_be(None)
    expect("flow_id" in result).to_be(True)

    mock_data = MagicMock()
    mock_data.serial_number = "test_serial"
    with (
        patch("zeversolar.ZeverSolarClient.get_data", return_value=mock_data),
        patch(
            "homeassistant.components.zeversolar.async_setup_entry",
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input={
                CONF_HOST: "test_ip",
            },
        )
        await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("already_configured")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
