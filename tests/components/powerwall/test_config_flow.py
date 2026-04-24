"""Test the Powerwall config flow."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from tesla_powerwall import (
    AccessDeniedError,
    MissingAttributeError,
    PowerwallUnreachableError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.powerwall.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.util import dt as dt_util

from ._fixtures import (
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_setup_entry as mock_setup_entry_fx,
)
from .mocks import (
    MOCK_GATEWAY_DIN,
    _mock_powerwall_side_effect,
    _mock_powerwall_site_name,
    _mock_powerwall_with_fixtures,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture, mock_network

VALID_CONFIG = {CONF_IP_ADDRESS: "1.2.3.4", CONF_PASSWORD: "00GGX"}


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf_fx),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network, zeroconf, and setup_entry for every test."""


@test
async def form_source_user(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get config flow setup form as a user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_powerwall = await _mock_powerwall_site_name(hass, "MySite")

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("MySite")
    expect(result2["data"]).to_equal(VALID_CONFIG)


@test.cases(
    test.case("powerwall_unreachable", exc=PowerwallUnreachableError),
    test.case("timeout", exc=TimeoutError),
)
async def form_cannot_connect(
    exc: type[Exception],
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_powerwall = await _mock_powerwall_side_effect(site_info=exc)

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_IP_ADDRESS: "cannot_connect"})


@test
async def invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_powerwall = await _mock_powerwall_side_effect(
        site_info=AccessDeniedError("any")
    )

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_PASSWORD: "invalid_auth"})


@test
async def form_unknown_exception(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle an unknown exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_powerwall = await _mock_powerwall_side_effect(site_info=ValueError)

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_CONFIG
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_wrong_version(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we can handle wrong version error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_powerwall = await _mock_powerwall_side_effect(
        site_info=MissingAttributeError({}, "")
    )

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({"base": "wrong_version"})


@test
async def already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we abort when already configured."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={CONF_IP_ADDRESS: "1.1.1.1"})
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="1.1.1.1",
            macaddress="aabbcceeddff",
            hostname="any",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def already_configured_with_ignored(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test ignored entries do not break checking for existing entries."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={}, source=config_entries.SOURCE_IGNORE
    )
    config_entry.add_to_hass(hass)

    mock_powerwall = await _mock_powerwall_site_name(hass, "Some site")

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.1.1.1",
                macaddress="aabbcceeddff",
                hostname="00GGX",
            ),
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Some site")
    expect(result2["data"]).to_equal({"ip_address": "1.1.1.1", "password": "00GGX"})


@test
async def dhcp_discovery_manual_configure(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can process the discovery from dhcp and manually configure."""
    mock_powerwall = await _mock_powerwall_site_name(hass, "Some site")

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall.login",
        side_effect=AccessDeniedError("xyz"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.1.1.1",
                macaddress="aabbcceeddff",
                hostname="any",
            ),
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Some site")
    expect(result2["data"]).to_equal(VALID_CONFIG)


@test
async def dhcp_discovery_auto_configure(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can process the discovery from dhcp and auto configure."""
    mock_powerwall = await _mock_powerwall_site_name(hass, "Some site")

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.1.1.1",
                macaddress="aabbcceeddff",
                hostname="00GGX",
            ),
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Some site")
    expect(result2["data"]).to_equal({"ip_address": "1.1.1.1", "password": "00GGX"})


@test
async def dhcp_discovery_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can process the discovery from dhcp and we cannot connect."""
    mock_powerwall = await _mock_powerwall_side_effect(
        site_info=PowerwallUnreachableError
    )

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.1.1.1",
                macaddress="aabbcceeddff",
                hostname="00GGX",
            ),
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def form_reauth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauthenticate."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id=MOCK_GATEWAY_DIN,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    flow = hass.config_entries.flow.async_get(result["flow_id"])
    expect(flow["context"]["title_placeholders"]).to_equal(
        {
            "ip_address": VALID_CONFIG[CONF_IP_ADDRESS],
            "name": entry.title,
        }
    )

    mock_powerwall = await _mock_powerwall_site_name(hass, "My site")

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "new-test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def dhcp_discovery_update_ip_address(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can update the ip address from dhcp."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id=MOCK_GATEWAY_DIN,
    )
    entry.add_to_hass(hass)
    mock_powerwall = MagicMock(login=MagicMock(side_effect=PowerwallUnreachableError))
    mock_powerwall.__aenter__.return_value = mock_powerwall

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.1.1.1",
                macaddress="aabbcceeddff",
                hostname=MOCK_GATEWAY_DIN.lower(),
            ),
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal("1.1.1.1")


@test
async def dhcp_discovery_does_not_update_ip_when_auth_fails(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we do not switch to another interface when auth is failing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id=MOCK_GATEWAY_DIN,
    )
    entry.add_to_hass(hass)
    mock_powerwall = MagicMock(login=MagicMock(side_effect=AccessDeniedError("any")))

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.1.1.1",
                macaddress="aabbcceeddff",
                hostname=MOCK_GATEWAY_DIN.lower(),
            ),
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal("1.2.3.4")


@test
async def dhcp_discovery_does_not_update_ip_when_auth_successful(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we do not switch to another interface when auth is successful."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id=MOCK_GATEWAY_DIN,
    )
    entry.add_to_hass(hass)
    mock_powerwall = MagicMock(login=MagicMock(return_value=True))

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.1.1.1",
                macaddress="aabbcceeddff",
                hostname=MOCK_GATEWAY_DIN.lower(),
            ),
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal("1.2.3.4")


@test
async def dhcp_discovery_updates_unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can update the unique id from dhcp."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id="1.2.3.4",
    )
    entry.add_to_hass(hass)
    mock_powerwall = await _mock_powerwall_site_name(hass, "Some site")

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.2.3.4",
                macaddress="aabbcceeddff",
                hostname=MOCK_GATEWAY_DIN.lower(),
            ),
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal("1.2.3.4")
    expect(entry.unique_id).to_equal(MOCK_GATEWAY_DIN)


@test
async def dhcp_discovery_updates_unique_id_when_entry_is_failed(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can update the unique id from dhcp in a failed state."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id="1.2.3.4",
    )
    entry.add_to_hass(hass)
    entry.mock_state(hass, ConfigEntryState.SETUP_ERROR)
    mock_powerwall = await _mock_powerwall_site_name(hass, "Some site")

    with patch(
        "homeassistant.components.powerwall.config_flow.Powerwall",
        return_value=mock_powerwall,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.2.3.4",
                macaddress="aabbcceeddff",
                hostname=MOCK_GATEWAY_DIN.lower(),
            ),
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal("1.2.3.4")
    expect(entry.unique_id).to_equal(MOCK_GATEWAY_DIN)


@test
async def discovered_wifi_does_not_update_ip_if_is_still_online(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a discovery does not update the ip unless the powerwall at the old ip is offline."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id=MOCK_GATEWAY_DIN,
    )
    entry.add_to_hass(hass)
    mock_powerwall = await _mock_powerwall_with_fixtures(hass)

    with (
        patch(
            "homeassistant.components.powerwall.config_flow.Powerwall",
            return_value=mock_powerwall,
        ),
        patch(
            "homeassistant.components.powerwall.Powerwall",
            return_value=mock_powerwall,
        ),
    ):
        expect(bool(await hass.config_entries.async_setup(entry.entry_id))).to_be(True)
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.2.3.5",
                macaddress="aabbcceeddff",
                hostname=MOCK_GATEWAY_DIN.lower(),
            ),
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal("1.2.3.4")


@test
async def discovered_wifi_does_not_update_ip_online_but_access_denied(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a discovery does not update the ip unless the powerwall at the old ip is offline."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id=MOCK_GATEWAY_DIN,
    )
    entry.add_to_hass(hass)
    mock_powerwall = await _mock_powerwall_with_fixtures(hass)
    mock_powerwall_no_access = await _mock_powerwall_with_fixtures(hass)
    mock_powerwall_no_access.login.side_effect = AccessDeniedError("any")

    with (
        patch(
            "homeassistant.components.powerwall.config_flow.Powerwall",
            return_value=mock_powerwall_no_access,
        ),
        patch(
            "homeassistant.components.powerwall.Powerwall",
            return_value=mock_powerwall,
        ),
    ):
        expect(bool(await hass.config_entries.async_setup(entry.entry_id))).to_be(True)
        await hass.async_block_till_done()

        mock_powerwall.get_meters.side_effect = TimeoutError
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=60))
        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="1.2.3.5",
                macaddress="aabbcceeddff",
                hostname=MOCK_GATEWAY_DIN.lower(),
            ),
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal("1.2.3.4")
