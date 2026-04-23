"""Test the Philips TV config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import ANY, AsyncMock

from haphilipsjs import PairingFailure, PhilipsTV
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.philips_js.const import CONF_ALLOW_NOTIFY, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import (
    MOCK_CONFIG,
    MOCK_CONFIG_PAIRED,
    MOCK_HOSTNAME,
    MOCK_NAME,
    MOCK_SERIAL_NO,
    MOCK_SYSTEM,
    MOCK_USERINPUT,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_setup_entry as mock_setup_entry_fx,
    mock_tv as mock_tv_fx,
    mock_tv_pairable as mock_tv_pairable_fx,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _tv: PhilipsTV = Depends(mock_tv_fx),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network, mock_tv, mock_setup_entry for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USERINPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Philips TV (1234567890)")
    expect(result2["data"]).to_equal(MOCK_CONFIG)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_tv: PhilipsTV = Depends(mock_tv_fx),
) -> None:
    """Test the reauth flow."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_NAME, unique_id=MOCK_SERIAL_NO
    )
    mock_config_entry.add_to_hass(hass)

    mock_tv.system = changed_system = {**MOCK_SYSTEM, "model": "changed"}

    expect(bool(await hass.config_entries.async_setup(mock_config_entry.entry_id))).to_be(True)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USERINPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(MOCK_CONFIG | {"system": changed_system})
    expect(len(mock_setup_entry.mock_calls)).to_equal(2)


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_tv: PhilipsTV = Depends(mock_tv_fx),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_tv.system = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USERINPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def pairing(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_tv_pairable: PhilipsTV = Depends(mock_tv_pairable_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test pairing flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USERINPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_tv_pairable.setTransport.assert_called_with(True, ANY)
    mock_tv_pairable.pairRequest.assert_called()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": "1234"}
    )

    expect(result).to_equal(
        {
            "context": {
                "source": "user",
                "unique_id": "ABCDEFGHIJKLF",
                "title_placeholders": {"name": "Philips TV"},
            },
            "flow_id": ANY,
            "type": "create_entry",
            "description": None,
            "description_placeholders": None,
            "handler": "philips_js",
            "result": ANY,
            "title": "55PUS7181/12 (ABCDEFGHIJKLF)",
            "data": MOCK_CONFIG_PAIRED,
            "version": 1,
            "options": {},
            "minor_version": 1,
            "subentries": (),
        }
    )

    await hass.async_block_till_done()
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def pair_request_failed(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_tv_pairable: PhilipsTV = Depends(mock_tv_pairable_fx),
) -> None:
    """Test pair request failure."""
    mock_tv_pairable.pairRequest.side_effect = PairingFailure({})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USERINPUT,
    )

    expect(result).to_equal(
        {
            "flow_id": ANY,
            "description_placeholders": {"error_id": None},
            "handler": "philips_js",
            "reason": "pairing_failure",
            "type": "abort",
        }
    )


@test
async def pair_grant_failed(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_tv_pairable: PhilipsTV = Depends(mock_tv_pairable_fx),
) -> None:
    """Test pair grant failure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USERINPUT,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_tv_pairable.setTransport.assert_called_with(True, ANY)
    mock_tv_pairable.pairRequest.assert_called()

    mock_tv_pairable.pairGrant.side_effect = PairingFailure({"error_id": "INVALID_PIN"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": "1234"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"pin": "invalid_pin"})

    mock_tv_pairable.pairGrant.side_effect = PairingFailure({})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": "1234"}
    )

    expect(result).to_equal(
        {
            "flow_id": ANY,
            "description_placeholders": {"error_id": None},
            "handler": "philips_js",
            "reason": "pairing_failure",
            "type": "abort",
        }
    )


@test
async def options_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="123456",
        data=MOCK_CONFIG_PAIRED,
    )
    config_entry.add_to_hass(hass)

    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_ALLOW_NOTIFY: True}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_ALLOW_NOTIFY: True})


@test.cases(
    test.case("secured", True, "_philipstv_s_rpc._tcp.local."),
    test.case("unsecured", False, "_philipstv_rpc._tcp.local."),
)
async def zeroconf_discovery(
    secured_transport: bool,
    discovery_type: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_tv_pairable: PhilipsTV = Depends(mock_tv_pairable_fx),
) -> None:
    """Test we can setup from zeroconf discovery."""
    mock_tv_pairable.secured_transport = secured_transport
    mock_tv_pairable.api_version_detected = 6
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname=MOCK_HOSTNAME,
            name=MOCK_NAME,
            port=None,
            properties={},
            type=discovery_type,
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_tv_pairable.setTransport.assert_called_with(secured_transport, 6)
    mock_tv_pairable.pairRequest.assert_called()


@test
async def zeroconf_probe_failed(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_tv_pairable: PhilipsTV = Depends(mock_tv_pairable_fx),
) -> None:
    """Test zeroconf flow abort when probe fails."""
    mock_tv_pairable.system = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname=MOCK_HOSTNAME,
            name=MOCK_NAME,
            port=None,
            properties={},
            type="_philipstv_s_rpc._tcp.local.",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("discovery_failure")
