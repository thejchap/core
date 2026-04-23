"""Test the epson config flow."""

from unittest.mock import MagicMock, patch

from epson_projector.const import PWR_OFF_STATE
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.epson.const import CONF_CONNECTION_TYPE, DOMAIN, HTTP
from homeassistant.const import CONF_HOST, CONF_NAME, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.epson._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we get the form."""
    with patch("homeassistant.components.epson.Projector.get_power", return_value="01"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)
    with (
        patch(
            "homeassistant.components.epson.Projector.get_power",
            return_value="01",
        ),
        patch(
            "homeassistant.components.epson.Projector.get_serial_number",
            return_value="12345",
        ),
        patch(
            "homeassistant.components.epson.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.epson.Projector.close",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_NAME: "test-epson"},
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("test-epson")
    expect(result2["data"]).to_equal({CONF_CONNECTION_TYPE: HTTP, CONF_HOST: "1.1.1.1"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.epson.Projector.get_power",
        return_value=STATE_UNAVAILABLE,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_NAME: "test-epson"},
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_powered_off(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we handle powered off during initial configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.epson.Projector.get_power",
        return_value=PWR_OFF_STATE,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_NAME: "test-epson"},
        )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "powered_off"})
