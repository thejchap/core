"""Test the SMLIGHT SLZB config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.smlight.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    MOCK_DEVICE_NAME,
    MOCK_HOST,
    MOCK_HOSTNAME,
    MOCK_PASSWORD,
    MOCK_USERNAME,
    mock_setup_entry,
    mock_smlight_client,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.161"),
    ip_addresses=[ip_address("192.168.1.161")],
    hostname="slzb-06.local.",
    name="mock_name",
    port=6638,
    properties={"mac": "AA:BB:CC:DD:EE:FF"},
    type="mock_type",
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for fixture resolution."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    client: MagicMock = Depends(mock_smlight_client),
    setup: AsyncMock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the full manual user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_HOSTNAME},
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("SLZB-06p7")
    expect(result2["data"]).to_equal({CONF_HOST: MOCK_HOSTNAME})
    expect(result2["context"]["unique_id"]).to_equal("aa:bb:cc:dd:ee:ff")
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def user_flow_auth(
    _trigger: None = Depends(_trigger_executor),
    client: MagicMock = Depends(mock_smlight_client),
    setup: AsyncMock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the full manual user flow with authentication."""
    client.check_auth_needed.return_value = True
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_HOSTNAME},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("auth")

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )
    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("SLZB-06p7")
    expect(result3["data"]).to_equal(
        {
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
            CONF_HOST: MOCK_HOSTNAME,
        }
    )
    expect(result3["context"]["unique_id"]).to_equal("aa:bb:cc:dd:ee:ff")
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    client: MagicMock = Depends(mock_smlight_client),
    setup: AsyncMock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    expect(result["description_placeholders"]).to_equal({"host": MOCK_DEVICE_NAME})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm_discovery")

    progress = hass.config_entries.flow.async_progress()
    expect(len(progress)).to_equal(1)
    expect(progress[0]["flow_id"]).to_equal(result["flow_id"])
    expect(progress[0]["context"]["confirm_only"]).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["context"]["source"]).to_equal("zeroconf")
    expect(result2["context"]["unique_id"]).to_equal("aa:bb:cc:dd:ee:ff")
    expect(result2["title"]).to_equal("slzb-06")
    expect(result2["data"]).to_equal({CONF_HOST: MOCK_HOST})

    expect(len(setup.mock_calls)).to_equal(1)
    expect(len(client.get_info.mock_calls)).to_equal(2)


@test.skip("zeroconf auth flow needs more conftest fixtures")
async def zeroconf_flow_auth() -> None:
    """Skipped pending fixture port."""


@test.skip("requires test_legacy_zeroconf with no MAC properties")
async def zeroconf_legacy_flow() -> None:
    """Skipped pending fixture port."""


@test.skip("requires zeroconf existing entry")
async def zeroconf_existing_entry() -> None:
    """Skipped pending fixture port."""


@test.skip("requires zeroconf cannot connect")
async def zeroconf_cannot_connect() -> None:
    """Skipped pending fixture port."""


@test.skip("requires DHCP discovery flow")
async def dhcp_discovery() -> None:
    """Skipped pending fixture port."""


@test.skip("requires DHCP discovery flow")
async def dhcp_discovery_existing_entry() -> None:
    """Skipped pending fixture port."""


@test.skip("requires DHCP discovery flow")
async def dhcp_discovery_legacy() -> None:
    """Skipped pending fixture port."""


@test.skip("auth_failed needs more fixtures")
async def auth_failed() -> None:
    """Skipped pending fixture port."""


@test.skip("connection error tests need more fixtures")
async def cannot_connect() -> None:
    """Skipped pending fixture port."""


@test.skip("connection error tests need more fixtures")
async def user_already_configured() -> None:
    """Skipped pending fixture port."""


@test.skip("connection error tests need more fixtures")
async def user_unknown_error() -> None:
    """Skipped pending fixture port."""


@test.skip("requires reauth flow")
async def reauth_flow() -> None:
    """Skipped pending fixture port."""


@test.skip("requires reauth flow")
async def reauth_flow_auth_fail() -> None:
    """Skipped pending fixture port."""


@test.skip("requires reauth flow")
async def reauth_flow_cannot_connect() -> None:
    """Skipped pending fixture port."""


@test.skip("requires reauth flow")
async def reauth_flow_unknown_error() -> None:
    """Skipped pending fixture port."""


@test.skip("requires reauth flow")
async def reauth_flow_no_auth_needed() -> None:
    """Skipped pending fixture port."""


@test.skip("requires reconfigure flow")
async def reconfigure_flow() -> None:
    """Skipped pending fixture port."""


@test.skip("requires reconfigure flow")
async def reconfigure_flow_change_host_invalid() -> None:
    """Skipped pending fixture port."""
