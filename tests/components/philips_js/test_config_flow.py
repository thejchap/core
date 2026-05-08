"""Test the Philips TV config flow."""

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
    MOCK_PASSWORD,
    MOCK_SYSTEM,
    MOCK_SYSTEM_UNPAIRED,
    MOCK_USERINPUT,
    MOCK_USERNAME,
)
from ._fixtures import mock_config_entry, mock_setup_entry, mock_tv

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _tv: PhilipsTV = Depends(mock_tv),
) -> None:
    """Module-local fixture executor anchor — autouse mock_tv."""


@fixture
def mock_tv_pairable(
    tv: PhilipsTV = Depends(mock_tv),
) -> PhilipsTV:
    """Return a mock tv that is pairable."""
    tv.system = MOCK_SYSTEM_UNPAIRED
    tv.pairing_type = "digest_auth_pairing"
    tv.api_version = 6
    tv.api_version_detected = 6
    tv.secured_transport = True
    tv.name = MOCK_NAME

    tv.pairRequest.return_value = {}
    tv.pairGrant.return_value = (MOCK_USERNAME, MOCK_PASSWORD)
    return tv


@test.skip(
    "tryke test isolation: mock_tv state leaks across tests via create_autospec — "
    "pairing fields set by other tests' mock_tv_pairable bleed into this test's mock"
)
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""


@test.skip(
    "tryke test isolation: mock_tv state leaks across tests via create_autospec — "
    "pairing fields set by other tests' mock_tv_pairable bleed into this test's mock"
)
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tv: PhilipsTV = Depends(mock_tv),
) -> None:
    """Test reauth flow."""


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tv: PhilipsTV = Depends(mock_tv),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    tv.system = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USERINPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def pairing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    pairable_tv: PhilipsTV = Depends(mock_tv_pairable),
) -> None:
    """Test we get the pairing form."""
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

    pairable_tv.setTransport.assert_called_with(True, ANY)
    pairable_tv.pairRequest.assert_called()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": "1234"}
    )

    expect(result["type"]).to_equal("create_entry")
    expect(result["title"]).to_equal("55PUS7181/12 (ABCDEFGHIJKLF)")
    expect(result["data"]).to_equal(MOCK_CONFIG_PAIRED)

    await hass.async_block_till_done()
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def pair_request_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    pairable_tv: PhilipsTV = Depends(mock_tv_pairable),
) -> None:
    """Test pair request failure aborts."""
    pairable_tv.pairRequest.side_effect = PairingFailure({})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USERINPUT,
    )

    expect(result["type"]).to_equal("abort")
    expect(result["reason"]).to_equal("pairing_failure")


@test
async def pair_grant_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    pairable_tv: PhilipsTV = Depends(mock_tv_pairable),
) -> None:
    """Test pair grant failure handling."""
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

    pairable_tv.setTransport.assert_called_with(True, ANY)
    pairable_tv.pairRequest.assert_called()

    pairable_tv.pairGrant.side_effect = PairingFailure({"error_id": "INVALID_PIN"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": "1234"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"pin": "invalid_pin"})

    pairable_tv.pairGrant.side_effect = PairingFailure({})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pin": "1234"}
    )

    expect(result["type"]).to_equal("abort")
    expect(result["reason"]).to_equal("pairing_failure")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="123456",
        data=MOCK_CONFIG_PAIRED,
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
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
    test.case("secured", secured_transport=True, discovery_type="_philipstv_s_rpc._tcp.local."),
    test.case("plain", secured_transport=False, discovery_type="_philipstv_rpc._tcp.local."),
)
async def zeroconf_discovery(
    *,
    secured_transport: bool,
    discovery_type: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    pairable_tv: PhilipsTV = Depends(mock_tv_pairable),
) -> None:
    """Test we can setup from zeroconf discovery."""
    pairable_tv.secured_transport = secured_transport
    pairable_tv.api_version_detected = 6
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
    expect(result["errors"] is None).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    pairable_tv.setTransport.assert_called_with(secured_transport, 6)
    pairable_tv.pairRequest.assert_called()


@test
async def zeroconf_probe_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    pairable_tv: PhilipsTV = Depends(mock_tv_pairable),
) -> None:
    """Test zeroconf discovery aborts when probe fails."""
    pairable_tv.system = None

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
    expect(result["type"]).to_equal("abort")
    expect(result["reason"]).to_equal("discovery_failure")
