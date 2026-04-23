"""Test the Nmap Tracker config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.device_tracker import (
    CONF_CONSIDER_HOME,
    CONF_SCAN_INTERVAL,
)
from homeassistant.components.nmap_tracker.const import (
    CONF_HOME_INTERVAL,
    CONF_HOSTS_EXCLUDE,
    CONF_HOSTS_LIST,
    CONF_MAC_EXCLUDE,
    CONF_OPTIONS,
    DEFAULT_OPTIONS,
    DOMAIN,
)
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test.cases(
    test.case("single_host", ["1.1.1.1"]),
    test.case("cidr", ["192.168.1.0/24"]),
    test.case("multi_cidr", ["192.168.1.0/24", "192.168.2.0/24"]),
)
async def form(
    hosts: list[str],
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    schema_defaults = result["data_schema"]({})
    expect(CONF_SCAN_INTERVAL in schema_defaults).to_be(False)

    with patch(
        "homeassistant.components.nmap_tracker.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOSTS_LIST: hosts,
                CONF_HOME_INTERVAL: 3,
                CONF_OPTIONS: DEFAULT_OPTIONS,
                CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
                CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(f"Nmap Tracker {', '.join(hosts)}")
    expect(result2["data"]).to_equal({})
    expect(result2["options"]).to_equal(
        {
            CONF_HOSTS_LIST: hosts,
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_range(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form and can take an ip range."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.nmap_tracker.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOSTS_LIST: ["192.168.0.5-12"],
                CONF_HOME_INTERVAL: 3,
                CONF_OPTIONS: DEFAULT_OPTIONS,
                CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
                CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Nmap Tracker 192.168.0.5-12")
    expect(result2["data"]).to_equal({})
    expect(result2["options"]).to_equal(
        {
            CONF_HOSTS_LIST: ["192.168.0.5-12"],
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_hosts(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid hosts passed in."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOSTS_LIST: ["not an ip block"],
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_HOSTS_EXCLUDE: [],
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_HOSTS_LIST: "invalid_hosts"})


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test duplicate host list."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_HOSTS_LIST: ["192.168.0.0/20"],
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
        },
    )
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOSTS_LIST: ["192.168.0.0/20"],
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_HOSTS_EXCLUDE: [],
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def form_invalid_ip_excludes(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid ip excludes passed in."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOSTS_LIST: ["3.3.3.3"],
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_HOSTS_EXCLUDE: ["not an exclude"],
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_HOSTS_EXCLUDE: "invalid_hosts"})


@test.cases(
    test.case("numeric", ["1234567890"]),
    test.case("mixed", ["1234567890", "11:22:33:44:55:66"]),
    test.case("letters", ["ABCDEFGHIJK"]),
)
async def form_invalid_mac_excludes(
    mac_excludes: list[str],
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid mac excludes passed in."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOSTS_LIST: ["3.3.3.3"],
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
            CONF_MAC_EXCLUDE: mac_excludes,
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_MAC_EXCLUDE: "invalid_hosts"})


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can edit options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_HOSTS_LIST: ["192.168.1.0/24"],
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00", "11:22:33:44:55:66"],
        },
        version=1,
        minor_version=2,
    )
    config_entry.add_to_hass(hass)
    hass.set_state(CoreState.stopped)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    expect(result["data_schema"]({})).to_equal(
        {
            CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
            CONF_HOME_INTERVAL: 3,
            CONF_HOSTS_LIST: ["192.168.1.0/24"],
            CONF_CONSIDER_HOME: 180,
            CONF_SCAN_INTERVAL: 120,
            CONF_OPTIONS: "-n -sn -PR -T4 --min-rate 10 --host-timeout 5s",
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00", "11:22:33:44:55:66"],
        }
    )

    with patch(
        "homeassistant.components.nmap_tracker.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOSTS_LIST: ["192.168.1.0/24", "192.168.2.0/24"],
                CONF_HOME_INTERVAL: 5,
                CONF_CONSIDER_HOME: 500,
                CONF_OPTIONS: "-sn",
                CONF_HOSTS_EXCLUDE: ["4.4.4.4", "5.5.5.5"],
                CONF_SCAN_INTERVAL: 10,
                CONF_MAC_EXCLUDE: ["00:00:00:00:00:00", "11:22:33:44:55:66"],
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            CONF_HOSTS_LIST: ["192.168.1.0/24", "192.168.2.0/24"],
            CONF_HOME_INTERVAL: 5,
            CONF_CONSIDER_HOME: 500,
            CONF_OPTIONS: "-sn",
            CONF_HOSTS_EXCLUDE: ["4.4.4.4", "5.5.5.5"],
            CONF_SCAN_INTERVAL: 10,
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00", "11:22:33:44:55:66"],
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
