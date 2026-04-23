"""Test the AirTouch 4 config flow."""

from unittest.mock import AsyncMock, Mock, patch

from airtouch4pyapi.airtouch import AirTouch, AirTouchAc, AirTouchGroup, AirTouchStatus
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.airtouch4.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)
    mock_ac = AirTouchAc()
    mock_groups = AirTouchGroup()
    mock_airtouch = AirTouch("")
    mock_airtouch.UpdateInfo = AsyncMock()
    mock_airtouch.Status = AirTouchStatus.OK
    mock_airtouch.GetAcs = Mock(return_value=[mock_ac])
    mock_airtouch.GetGroups = Mock(return_value=[mock_groups])

    with (
        patch(
            "homeassistant.components.airtouch4.config_flow.AirTouch",
            return_value=mock_airtouch,
        ),
        patch(
            "homeassistant.components.airtouch4.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "0.0.0.1"}
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("0.0.0.1")
    expect(result2["data"]).to_equal({"host": "0.0.0.1"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_timeout(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test we handle a connection timeout."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mock_airtouch = AirTouch("")
    mock_airtouch.UpdateInfo = AsyncMock()
    mock_airtouch.status = AirTouchStatus.CONNECTION_INTERRUPTED
    with patch(
        "homeassistant.components.airtouch4.config_flow.AirTouch",
        return_value=mock_airtouch,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "0.0.0.1"}
        )
        expect(result2["type"] is FlowResultType.FORM).to_be(True)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_library_error_message(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test we handle an unknown error message from the library."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mock_airtouch = AirTouch("")
    mock_airtouch.UpdateInfo = AsyncMock()
    mock_airtouch.status = AirTouchStatus.ERROR
    with patch(
        "homeassistant.components.airtouch4.config_flow.AirTouch",
        return_value=mock_airtouch,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "0.0.0.1"}
        )
        expect(result2["type"] is FlowResultType.FORM).to_be(True)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_connection_refused(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test we handle a connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mock_airtouch = AirTouch("")
    mock_airtouch.UpdateInfo = AsyncMock()
    mock_airtouch.status = AirTouchStatus.NOT_CONNECTED
    with patch(
        "homeassistant.components.airtouch4.config_flow.AirTouch",
        return_value=mock_airtouch,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "0.0.0.1"}
        )
        expect(result2["type"] is FlowResultType.FORM).to_be(True)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_no_units(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test we handle no units found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mock_ac = AirTouchAc()
    mock_airtouch = AirTouch("")
    mock_airtouch.UpdateInfo = AsyncMock()
    mock_airtouch.Status = AirTouchStatus.OK
    mock_airtouch.GetAcs = Mock(return_value=[mock_ac])
    mock_airtouch.GetGroups = Mock(return_value=[])

    with patch(
        "homeassistant.components.airtouch4.config_flow.AirTouch",
        return_value=mock_airtouch,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "0.0.0.1"}
        )

        expect(result2["type"] is FlowResultType.FORM).to_be(True)
        expect(result2["errors"]).to_equal({"base": "no_units"})
