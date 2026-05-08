"""Test for DNS IP integration Init."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.dnsip.const import (
    CONF_HOSTNAME,
    CONF_IPV4,
    CONF_IPV6,
    CONF_PORT_IPV6,
    CONF_RESOLVER,
    CONF_RESOLVER_IPV6,
    DEFAULT_PORT,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant

from . import RetrieveDNS

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def load_unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test load and unload an entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_IPV4: True,
            CONF_IPV6: False,
        },
        options={
            CONF_RESOLVER: "208.67.222.222",
            CONF_RESOLVER_IPV6: "2620:119:53::53",
            CONF_PORT: 53,
            CONF_PORT_IPV6: 53,
        },
        entry_id="1",
        unique_id="home-assistant.io",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.config_flow.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def port_migration(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migration of the config entry from no ports to with ports."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_IPV4: True,
            CONF_IPV6: True,
        },
        options={
            CONF_RESOLVER: "208.67.222.222",
            CONF_RESOLVER_IPV6: "2620:119:53::53",
        },
        entry_id="1",
        unique_id="home-assistant.io",
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.sensor.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.version).to_equal(1)
    expect(entry.minor_version).to_equal(3)
    expect(entry.options[CONF_PORT]).to_equal(DEFAULT_PORT)
    expect(entry.options[CONF_PORT_IPV6]).to_equal(DEFAULT_PORT)
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def remove_unique_id_migration(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migration of the config entry removing the unique_id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_IPV4: True,
            CONF_IPV6: True,
        },
        options={
            CONF_RESOLVER: "208.67.222.222",
            CONF_RESOLVER_IPV6: "2620:119:53::53",
            CONF_PORT: DEFAULT_PORT,
            CONF_PORT_IPV6: DEFAULT_PORT,
        },
        entry_id="1",
        unique_id="home-assistant.io",
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.sensor.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.version).to_equal(1)
    expect(entry.minor_version).to_equal(3)
    expect(entry.unique_id).to_be(None)
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def migrate_error_from_future(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a future version isn't migrated."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOSTNAME: "home-assistant.io",
            CONF_NAME: "home-assistant.io",
            CONF_IPV4: True,
            CONF_IPV6: True,
            "some_new_data": "new_value",
        },
        options={
            CONF_RESOLVER: "208.67.222.222",
            CONF_RESOLVER_IPV6: "2620:119:53::53",
        },
        entry_id="1",
        unique_id="home-assistant.io",
        version=2,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.dnsip.sensor.aiodns.DNSResolver",
        return_value=RetrieveDNS(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
