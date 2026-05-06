"""Test the Anthem A/V Receivers config flow."""

from unittest.mock import AsyncMock, patch

from anthemav.device_error import DeviceError
from tryke import Depends, expect, fixture, test

from homeassistant.components.anthemav.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_anthemav, mock_config_entry, mock_connection_create

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_with_valid_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connection: AsyncMock = Depends(mock_connection_create),
    _anthemav: AsyncMock = Depends(mock_anthemav),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.anthemav.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 14999,
            },
        )

        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Anthem AV")
    expect(result2["data"]).to_equal(
        {
            "host": "1.1.1.1",
            "port": 14999,
            "mac": "00:00:00:00:00:01",
            "model": "MRX 520",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_device_info_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle DeviceError from library."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "anthemav.Connection.create",
        side_effect=DeviceError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 14999,
            },
        )

        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_receive_deviceinfo"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "anthemav.Connection.create",
        side_effect=OSError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 14999,
            },
        )

        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def device_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connection: AsyncMock = Depends(mock_connection_create),
    _anthemav: AsyncMock = Depends(mock_anthemav),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we import existing configuration."""
    config = {
        "host": "1.1.1.1",
        "port": 14999,
    }

    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=config
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
