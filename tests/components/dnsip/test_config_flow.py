"""Test the DNS IP config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aiodns.error import DNSError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.dnsip.config_flow import DATA_SCHEMA, DATA_SCHEMA_ADV
from homeassistant.components.dnsip.const import (
    CONF_HOSTNAME,
    CONF_IPV4,
    CONF_IPV6,
    CONF_PORT_IPV6,
    CONF_RESOLVER,
    CONF_RESOLVER_IPV6,
    DEFAULT_HOSTNAME,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.dnsip import RetrieveDNS
from tests.components.dnsip._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["data_schema"] == DATA_SCHEMA).to_be(True)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
            return_value=RetrieveDNS(),
        ),
        patch(
            "homeassistant.components.dnsip.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOSTNAME: "home-assistant.io"},
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("home-assistant.io")
    expect(result2["data"]).to_equal(
        {
            "hostname": "home-assistant.io",
            "name": "home-assistant.io",
            "ipv4": True,
            "ipv6": True,
        }
    )
    expect(result2["options"]).to_equal(
        {
            "resolver": "208.67.222.222",
            "resolver_ipv6": "2620:119:53::53",
            "port": 53,
            "port_ipv6": 53,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_adv(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we get the form with advanced options on."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )

    expect(result["data_schema"] == DATA_SCHEMA_ADV).to_be(True)

    with (
        patch(
            "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
            return_value=RetrieveDNS(),
        ),
        patch(
            "homeassistant.components.dnsip.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOSTNAME: "home-assistant.io",
                CONF_RESOLVER: "8.8.8.8",
                CONF_RESOLVER_IPV6: "2620:119:53::53",
                CONF_PORT: 53,
                CONF_PORT_IPV6: 53,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("home-assistant.io")
    expect(result2["data"]).to_equal(
        {
            "hostname": "home-assistant.io",
            "name": "home-assistant.io",
            "ipv4": True,
            "ipv6": True,
        }
    )
    expect(result2["options"]).to_equal(
        {
            "resolver": "8.8.8.8",
            "resolver_ipv6": "2620:119:53::53",
            "port": 53,
            "port_ipv6": 53,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test validate url fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        side_effect=DNSError("Did not find"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOSTNAME: "home-assistant.io"},
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "invalid_hostname"})


@test
async def flow_already_exist(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test flow when unique id already exist."""
    MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_IPV4: True,
            CONF_IPV6: True,
        },
        options={
            CONF_RESOLVER: "208.67.222.222",
            CONF_RESOLVER_IPV6: "2620:119:53::5",
            CONF_PORT: 53,
            CONF_PORT_IPV6: 53,
        },
        unique_id="home-assistant.io",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    dns_mock = RetrieveDNS()
    with (
        patch(
            "homeassistant.components.dnsip.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
            return_value=dns_mock,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOSTNAME: "home-assistant.io"},
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test options config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_IPV4: True,
            CONF_IPV6: False,
        },
        options={
            CONF_RESOLVER: "208.67.222.222",
            CONF_RESOLVER_IPV6: "2620:119:53::5",
            CONF_PORT: 53,
            CONF_PORT_IPV6: 53,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RESOLVER: "8.8.8.8",
                CONF_RESOLVER_IPV6: "2001:4860:4860::8888",
                CONF_PORT: 53,
                CONF_PORT_IPV6: 53,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]).to_equal(
        {
            "resolver": "8.8.8.8",
            "resolver_ipv6": "2001:4860:4860::8888",
            "port": 53,
            "port_ipv6": 53,
        }
    )

    expect(entry.state is ConfigEntryState.LOADED).to_be(True)


@test
async def options_flow_empty_return(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test options config flow with empty return from user."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_IPV4: True,
            CONF_IPV6: False,
        },
        options={
            CONF_RESOLVER: "8.8.8.8",
            CONF_RESOLVER_IPV6: "2620:119:53::1",
            CONF_PORT: 53,
            CONF_PORT_IPV6: 53,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={},
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]).to_equal(
        {
            "resolver": "208.67.222.222",
            "resolver_ipv6": "2620:119:53::53",
            "port": 53,
            "port_ipv6": 53,
        }
    )

    entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(entry.data).to_equal(
        {
            "hostname": "home-assistant.io",
            "ipv4": True,
            "ipv6": False,
            "name": "home-assistant.io",
        }
    )
    expect(entry.options).to_equal(
        {
            "resolver": "208.67.222.222",
            "resolver_ipv6": "2620:119:53::53",
            "port": 53,
            "port_ipv6": 53,
        }
    )


@test.cases(
    test.case(
        "ipv4",
        {
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_RESOLVER: "208.67.222.222",
            CONF_RESOLVER_IPV6: "2620:119:53::5",
            CONF_PORT: 53,
            CONF_PORT_IPV6: 53,
            CONF_IPV4: True,
            CONF_IPV6: False,
        },
    ),
    test.case(
        "ipv6",
        {
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_RESOLVER: "208.67.222.222",
            CONF_RESOLVER_IPV6: "2620:119:53::5",
            CONF_PORT: 53,
            CONF_PORT_IPV6: 53,
            CONF_IPV4: False,
            CONF_IPV6: True,
        },
    ),
)
async def options_error(
    p_input: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test validate url fails in options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data=p_input,
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.async_setup_entry",
        return_value=True,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        side_effect=DNSError("Did not find"),
    ):
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_RESOLVER: "192.168.200.34",
                CONF_RESOLVER_IPV6: "2001:4860:4860::8888",
                CONF_PORT: 53,
                CONF_PORT_IPV6: 53,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["step_id"]).to_equal("init")
    if p_input[CONF_IPV4]:
        expect(result2["errors"]).to_equal({"resolver": "invalid_resolver"})
    if p_input[CONF_IPV6]:
        expect(result2["errors"]).to_equal({"resolver_ipv6": "invalid_resolver"})


@test
async def cannot_configure_options_for_myip(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test options config flow aborts for default myip hostname."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            CONF_HOSTNAME: DEFAULT_HOSTNAME,
            CONF_NAME: "myip",
            CONF_IPV4: True,
            CONF_IPV6: False,
        },
        options={
            CONF_RESOLVER: "208.67.222.222",
            CONF_RESOLVER_IPV6: "2620:119:53::5",
            CONF_PORT: 53,
            CONF_PORT_IPV6: 53,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("no_options")
