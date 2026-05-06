"""Test the wmspro config flow."""

from unittest.mock import AsyncMock, patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant.components.wmspro.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from . import setup_config_entry
from ._fixtures import (
    mock_config_entry,
    mock_dest_refresh,
    mock_hub_configuration_prod_awning_dimmer,
    mock_hub_configuration_test,
    mock_hub_ping,
    mock_hub_refresh,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _refresh: AsyncMock = Depends(mock_hub_refresh),
) -> None:
    """Test we can handle user-input to create a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1.2.3.4")
    expect(result["data"]).to_equal({CONF_HOST: "1.2.3.4"})
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def config_flow_from_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _refresh: AsyncMock = Depends(mock_hub_refresh),
) -> None:
    """Test we can handle DHCP discovery to create a config entry."""
    info = DhcpServiceInfo(
        ip="1.2.3.4", hostname="webcontrol", macaddress="001122334455"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=info
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1.2.3.4")
    expect(result["data"]).to_equal({CONF_HOST: "1.2.3.4"})
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def config_flow_from_dhcp_add_mac(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _refresh: AsyncMock = Depends(mock_hub_refresh),
) -> None:
    """Test we can use DHCP discovery to add MAC address to a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1.2.3.4")
    expect(result["data"]).to_equal({CONF_HOST: "1.2.3.4"})
    expect(len(setup.mock_calls)).to_equal(1)
    expect(hass.config_entries.async_entries(DOMAIN)[0].unique_id).to_be(None)

    info = DhcpServiceInfo(
        ip="1.2.3.4", hostname="webcontrol", macaddress="001122334455"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(hass.config_entries.async_entries(DOMAIN)[0].unique_id).to_equal(
        "00:11:22:33:44:55"
    )


@test
async def config_flow_from_dhcp_ip_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _refresh: AsyncMock = Depends(mock_hub_refresh),
) -> None:
    """Test we can use DHCP discovery to update IP in a config entry."""
    info = DhcpServiceInfo(
        ip="1.2.3.4", hostname="webcontrol", macaddress="001122334455"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=info
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1.2.3.4")
    expect(result["data"]).to_equal({CONF_HOST: "1.2.3.4"})
    expect(len(setup.mock_calls)).to_equal(1)
    expect(hass.config_entries.async_entries(DOMAIN)[0].unique_id).to_equal(
        "00:11:22:33:44:55"
    )

    info = DhcpServiceInfo(
        ip="5.6.7.8", hostname="webcontrol", macaddress="001122334455"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(hass.config_entries.async_entries(DOMAIN)[0].unique_id).to_equal(
        "00:11:22:33:44:55"
    )
    expect(hass.config_entries.async_entries(DOMAIN)[0].data[CONF_HOST]).to_equal(
        "5.6.7.8"
    )


@test
async def config_flow_from_dhcp_no_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _refresh: AsyncMock = Depends(mock_hub_refresh),
) -> None:
    """Test we do not use DHCP discovery to overwrite hostname with IP in config entry."""
    info = DhcpServiceInfo(
        ip="1.2.3.4", hostname="webcontrol", macaddress="001122334455"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=info
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "webcontrol",
            },
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("webcontrol")
    expect(result["data"]).to_equal({CONF_HOST: "webcontrol"})
    expect(len(setup.mock_calls)).to_equal(1)
    expect(hass.config_entries.async_entries(DOMAIN)[0].unique_id).to_equal(
        "00:11:22:33:44:55"
    )

    info = DhcpServiceInfo(
        ip="5.6.7.8", hostname="webcontrol", macaddress="001122334455"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(hass.config_entries.async_entries(DOMAIN)[0].unique_id).to_equal(
        "00:11:22:33:44:55"
    )
    expect(hass.config_entries.async_entries(DOMAIN)[0].data[CONF_HOST]).to_equal(
        "webcontrol"
    )


@test
async def config_flow_ping_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _refresh: AsyncMock = Depends(mock_hub_refresh),
) -> None:
    """Test we handle ping failed error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1.2.3.4")
    expect(result["data"]).to_equal({CONF_HOST: "1.2.3.4"})
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def config_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _refresh: AsyncMock = Depends(mock_hub_refresh),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        side_effect=aiohttp.ClientError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1.2.3.4")
    expect(result["data"]).to_equal({CONF_HOST: "1.2.3.4"})
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def config_flow_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _refresh: AsyncMock = Depends(mock_hub_refresh),
) -> None:
    """Test we handle an unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        side_effect=RuntimeError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1.2.3.4")
    expect(result["data"]).to_equal({CONF_HOST: "1.2.3.4"})
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def config_flow_duplicate_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _ping: AsyncMock = Depends(mock_hub_ping),
    _dest_refresh: AsyncMock = Depends(mock_dest_refresh),
    _config_test: AsyncMock = Depends(mock_hub_configuration_test),
) -> None:
    """Test we prevent creation of duplicate config entries."""
    await setup_config_entry(hass, config_entry)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "5.6.7.8"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def config_flow_multiple_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _ping: AsyncMock = Depends(mock_hub_ping),
    _dest_refresh: AsyncMock = Depends(mock_dest_refresh),
    config_test: AsyncMock = Depends(mock_hub_configuration_test),
    config_dimmer: AsyncMock = Depends(mock_hub_configuration_prod_awning_dimmer),
) -> None:
    """Test we allow creation of different config entries."""
    await setup_config_entry(hass, config_entry)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    config_dimmer.return_value = config_test.return_value

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "5.6.7.8"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("5.6.7.8")
    expect(result["data"]).to_equal({CONF_HOST: "5.6.7.8"})
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(2)
