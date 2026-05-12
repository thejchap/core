"""Test setting up and unloading PrusaLink."""

from datetime import timedelta
from unittest.mock import patch

from httpx import ConnectError
from pyprusalink.types import InvalidAuth, PrusaLinkError
from tryke import Depends, expect, fixture, test

from homeassistant.components.prusalink import DOMAIN
from homeassistant.components.prusalink.config_flow import ConfigFlow
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, issue_registry as ir
from homeassistant.util.dt import utcnow

from ._fixtures import (
    mock_api as mock_api_fixture,
    mock_config_entry as mock_config_entry_fixture,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def device_info(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    _api: None = Depends(mock_api_fixture),
) -> None:
    """Test device info is populated with serial number and firmware version."""
    device_registry = dr.async_get(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_config_entry.entry_id)}
    )
    expect(device).not_.to_be(None)
    assert device is not None
    expect(device.serial_number).to_equal("serial-1337")
    expect(device.sw_version).to_equal("6.1.2+11023")


@test
async def unloading(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    _api: None = Depends(mock_api_fixture),
) -> None:
    """Test unloading prusalink."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(hass.states.async_entity_ids_count() > 0).to_be(True)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    for state in hass.states.async_all():
        expect(state.state).to_equal("unavailable")


@test.cases(
    test.case("invalid_auth", exception=InvalidAuth),
    test.case("prusalink_error", exception=PrusaLinkError),
    test.case(
        "connect_error", exception=ConnectError("All connection attempts failed")
    ),
)
async def failed_update(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    _api: None = Depends(mock_api_fixture),
    *,
    exception: Exception,
) -> None:
    """Test failed update marks prusalink unavailable."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    with (
        patch(
            "homeassistant.components.prusalink.PrusaLink.get_version",
            side_effect=exception,
        ),
        patch(
            "homeassistant.components.prusalink.PrusaLink.get_status",
            side_effect=exception,
        ),
        patch(
            "homeassistant.components.prusalink.PrusaLink.get_legacy_printer",
            side_effect=exception,
        ),
        patch(
            "homeassistant.components.prusalink.PrusaLink.get_job",
            side_effect=exception,
        ),
    ):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30), fire_all=True)
        await hass.async_block_till_done()

    for state in hass.states.async_all():
        expect(state.state).to_equal("unavailable")


@test
async def migration_from_1_1_to_1_2(
    hass: HomeAssistant = Depends(_trigger_executor),
    _api: None = Depends(mock_api_fixture),
) -> None:
    """Test migrating from version 1 to 2."""
    data = {
        CONF_HOST: "http://prusaxl.local",
        CONF_API_KEY: "api-key",
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        version=1,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    issue_registry = ir.async_get(hass)
    config_entries = hass.config_entries.async_entries(DOMAIN)

    expect(len(config_entries)).to_equal(1)
    expect(config_entries[0].data).to_equal(
        {
            **data,
            CONF_USERNAME: "maker",
            CONF_PASSWORD: "api-key",
        }
    )
    expect(len(issue_registry.issues)).to_equal(0)


@test
async def migration_from_1_1_to_1_2_outdated_firmware(
    hass: HomeAssistant = Depends(_trigger_executor),
    _api: None = Depends(mock_api_fixture),
) -> None:
    """Test migrating from version 1.1 to 1.2."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "http://prusaxl.local",
            CONF_API_KEY: "api-key",
        },
        version=1,
    )
    entry.add_to_hass(hass)

    with patch(
        "pyprusalink.PrusaLink.get_info",
        side_effect=InvalidAuth,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    issue_registry = ir.async_get(hass)
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(entry.minor_version).to_equal(1)
    expect((DOMAIN, "firmware_5_1_required") in issue_registry.issues).to_be(True)

    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry.minor_version).to_equal(2)
    expect((DOMAIN, "firmware_5_1_required") in issue_registry.issues).to_be(False)


@test
async def migration_fails_on_future_version(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test migrating fails on a version higher than the current one."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        version=ConfigFlow.VERSION + 1,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
