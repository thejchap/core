"""Test the Radio Thermostat config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from radiotherm import CommonThermostat
from radiotherm.validate import RadiothermTstatError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.radiotherm.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


def _mock_radiotherm():
    tstat = MagicMock(autospec=CommonThermostat)
    tstat.name = {"raw": "My Name"}
    tstat.sys = {
        "raw": {"uuid": "aabbccddeeff", "fw_version": "1.2.3", "api_version": "4.5.6"}
    }
    tstat.model = {"raw": "Model"}
    return tstat


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.radiotherm.data.radiotherm.get_thermostat",
            return_value=_mock_radiotherm(),
        ),
        patch(
            "homeassistant.components.radiotherm.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.2.3.4"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("My Name")
    expect(result2["data"]).to_equal({"host": "1.2.3.4"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_unknown_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.radiotherm.data.radiotherm.get_thermostat",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.2.3.4"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.radiotherm.data.radiotherm.get_thermostat",
        side_effect=RadiothermTstatError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.2.3.4"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_HOST: "cannot_connect"})


@test
async def dhcp_can_confirm(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test DHCP discovery flow can confirm right away."""
    with patch(
        "homeassistant.components.radiotherm.data.radiotherm.get_thermostat",
        return_value=_mock_radiotherm(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                hostname="radiotherm",
                ip="1.2.3.4",
                macaddress="aabbccddeeff",
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            "host": "1.2.3.4",
            "name": "My Name",
            "model": "Model",
        }
    )

    with patch(
        "homeassistant.components.radiotherm.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("My Name")
    expect(result2["data"]).to_equal({"host": "1.2.3.4"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_fails_to_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test DHCP discovery flow that fails to connect."""
    with patch(
        "homeassistant.components.radiotherm.data.radiotherm.get_thermostat",
        side_effect=RadiothermTstatError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                hostname="radiotherm",
                ip="1.2.3.4",
                macaddress="aabbccddeeff",
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def dhcp_already_exists(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test DHCP discovery flow that fails to connect."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.radiotherm.data.radiotherm.get_thermostat",
        return_value=_mock_radiotherm(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                hostname="radiotherm",
                ip="1.2.3.4",
                macaddress="aabbccddeeff",
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_unique_id_already_exists(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creating an entry where the unique_id already exists."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.radiotherm.data.radiotherm.get_thermostat",
            return_value=_mock_radiotherm(),
        ),
        patch(
            "homeassistant.components.radiotherm.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.2.3.4"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
