"""Test the UPB Control config flow."""

from asyncio import TimeoutError
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.upb.const import DOMAIN
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def mocked_upb(sync_complete=True, config_ok=True):
    """Mock UPB lib."""

    def _add_handler(_, callback):
        callback()

    def _dummy_add_handler(_, _callback):
        pass

    upb_mock = AsyncMock()
    type(upb_mock).network_id = PropertyMock(return_value="42")
    type(upb_mock).config_ok = PropertyMock(return_value=config_ok)
    type(upb_mock).disconnect = MagicMock()
    type(upb_mock).add_handler = MagicMock()
    upb_mock.add_handler.side_effect = (
        _add_handler if sync_complete else _dummy_add_handler
    )
    return patch(
        "homeassistant.components.upb.config_flow.upb_lib.UpbPim", return_value=upb_mock
    )


async def valid_tcp_flow(
    hass: HomeAssistant, sync_complete: bool = True, config_ok: bool = True
) -> ConfigFlowResult:
    """Get result dict that are standard for most tests."""
    with (
        mocked_upb(sync_complete, config_ok),
        patch("homeassistant.components.upb.async_setup_entry", return_value=True),
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        return await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {"protocol": "TCP", "address": "1.2.3.4", "file_path": "upb.upe"},
        )


@test
async def full_upb_flow_with_serial_port(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a full UPB config flow with serial port."""
    with (
        mocked_upb(),
        patch(
            "homeassistant.components.upb.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {
                "protocol": "Serial port",
                "address": "/dev/ttyS0:115200",
                "file_path": "upb.upe",
            },
        )
        await hass.async_block_till_done()

    expect(flow["type"]).to_be(FlowResultType.FORM)
    expect(flow["errors"]).to_equal({})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("UPB")
    expect(result["data"]).to_equal(
        {
            "host": "serial:///dev/ttyS0:115200",
            "file_path": "upb.upe",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_user_with_tcp_upb(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup a serial upb."""
    result = await valid_tcp_flow(hass)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({"host": "tcp://1.2.3.4", "file_path": "upb.upe"})
    await hass.async_block_till_done()


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    with patch(
        "homeassistant.components.upb.config_flow.asyncio.timeout",
        side_effect=TimeoutError,
    ):
        result = await valid_tcp_flow(hass, sync_complete=False)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_missing_upb_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await valid_tcp_flow(hass, config_ok=False)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_upb_file"})


@test
async def form_user_with_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup a TCP upb."""
    _ = await valid_tcp_flow(hass)
    result2 = await valid_tcp_flow(hass)
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
    await hass.async_block_till_done()
