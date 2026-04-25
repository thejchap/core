"""Tests for the WiiM config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.wiim.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.network import NoURLAvailableError
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_probe_player,
    mock_setup_entry,
    setup_internal_url,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.100"),
    ip_addresses=[ip_address("192.168.1.100")],
    hostname="wiim-pro.local.",
    name="WiiM Pro._linkplay._tcp.local.",
    port=49152,
    properties={"uuid": "uuid:test-udn-1234"},
    type="_linkplay._tcp.local.",
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _url: None = Depends(setup_internal_url),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user_flow_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _probe: AsyncMock = Depends(mock_probe_player),
) -> None:
    """Test the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("WiiM Pro")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100"})
    expect(result["result"].unique_id).to_equal("uuid:test-udn-1234")


@test
async def user_flow_abort_when_homeassistant_url_missing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    probe: AsyncMock = Depends(mock_probe_player),
) -> None:
    """Test the user flow aborts before probing when no URL is available."""
    with patch(
        "homeassistant.components.wiim.util.get_url",
        side_effect=NoURLAvailableError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("missing_homeassistant_url")
    probe.assert_not_called()


@test
async def user_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    probe: AsyncMock = Depends(mock_probe_player),
) -> None:
    """Test the user flow handles connection failures."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    probe.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    probe.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_no_probe(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    probe: AsyncMock = Depends(mock_probe_player),
) -> None:
    """Test the user flow handles connection failures."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    old_return_value = probe.return_value
    probe.return_value = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    probe.return_value = old_return_value

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _probe: AsyncMock = Depends(mock_probe_player),
) -> None:
    """Test the user flow aborts for an already configured device."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _probe: AsyncMock = Depends(mock_probe_player),
) -> None:
    """Test the zeroconf discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(result["description_placeholders"]).to_equal({"name": "WiiM Pro"})

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("WiiM Pro")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100"})
    expect(result["result"].unique_id).to_equal("uuid:test-udn-1234")


@test
async def zeroconf_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    probe: AsyncMock = Depends(mock_probe_player),
) -> None:
    """Test the zeroconf flow aborts on connection errors."""
    probe.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def zeroconf_flow_no_probe(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    probe: AsyncMock = Depends(mock_probe_player),
) -> None:
    """Test the zeroconf flow aborts when probing failed."""
    probe.return_value = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def zeroconf_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the zeroconf flow aborts for an already configured device."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.101"),
            ip_addresses=[ip_address("192.168.1.101")],
            hostname="wiim-pro.local.",
            name="WiiM Pro._linkplay._tcp.local.",
            port=49152,
            properties={"uuid": "uuid:test-udn-1234"},
            type="_linkplay._tcp.local.",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.101")
