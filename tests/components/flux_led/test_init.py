"""Tests for the flux_led component."""

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import flux_led
from homeassistant.components.flux_led.const import (
    CONF_REMOTE_ACCESS_ENABLED,
    CONF_REMOTE_ACCESS_HOST,
    CONF_REMOTE_ACCESS_PORT,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    CONF_HOST,
    CONF_NAME,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from . import (
    DEFAULT_ENTRY_TITLE,
    DHCP_DISCOVERY,
    FLUX_DISCOVERY,
    FLUX_DISCOVERY_PARTIAL,
    IP_ADDRESS,
    MAC_ADDRESS,
    MAC_ADDRESS_ONE_OFF,
    _mocked_bulb,
    _patch_discovery,
    _patch_wifibulb,
)
from ._fixtures import (
    mock_multiple_broadcast_addresses,
    mock_single_broadcast_address,
    translations,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def configuring_flux_led_causes_discovery(
    _trigger: None = Depends(_trigger_executor),
    _broadcast: None = Depends(mock_single_broadcast_address),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that specifying empty config does discovery."""
    with (
        patch(
            "homeassistant.components.flux_led.discovery.AIOBulbScanner.async_scan"
        ) as scan,
        patch(
            "homeassistant.components.flux_led.discovery.AIOBulbScanner.getBulbInfo"
        ) as discover,
    ):
        discover.return_value = [FLUX_DISCOVERY]
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()

        expect(len(scan.mock_calls)).to_equal(1)

        async_fire_time_changed(hass, utcnow() + flux_led.DISCOVERY_INTERVAL)
        await hass.async_block_till_done()
        expect(len(scan.mock_calls)).to_equal(2)


@test
async def configuring_flux_led_causes_discovery_multiple_addresses(
    _trigger: None = Depends(_trigger_executor),
    _broadcast: None = Depends(mock_multiple_broadcast_addresses),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that specifying empty config does discovery."""
    with (
        patch(
            "homeassistant.components.flux_led.discovery.AIOBulbScanner.async_scan"
        ) as scan,
        patch(
            "homeassistant.components.flux_led.discovery.AIOBulbScanner.getBulbInfo"
        ) as discover,
    ):
        discover.return_value = [FLUX_DISCOVERY]
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(len(scan.mock_calls)).to_equal(2)

        async_fire_time_changed(hass, utcnow() + flux_led.DISCOVERY_INTERVAL)
        await hass.async_block_till_done()
        expect(len(scan.mock_calls)).to_equal(4)


@test
async def config_entry_reload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that a config entry can be reloaded."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS}, unique_id=MAC_ADDRESS
    )
    config_entry.add_to_hass(hass)
    with _patch_discovery(), _patch_wifibulb():
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)
        await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_retry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that a config entry can be retried."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS}, unique_id=MAC_ADDRESS
    )
    config_entry.add_to_hass(hass)
    with _patch_discovery(no_device=True), _patch_wifibulb(no_device=True):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def config_entry_retry_right_away_on_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery makes the config entry reload if its in a retry state."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS}, unique_id=MAC_ADDRESS
    )
    config_entry.add_to_hass(hass)
    with _patch_discovery(no_device=True), _patch_wifibulb(no_device=True):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    with _patch_discovery(), _patch_wifibulb():
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_DISCOVERY,
        )
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def coordinator_retry_right_away_on_discovery_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test discovery makes the coordinator force poll if its already setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS, CONF_NAME: DEFAULT_ENTRY_TITLE},
        unique_id=MAC_ADDRESS,
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    with _patch_discovery(), _patch_wifibulb(device=bulb):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    entity_id = "light.bulb_rgbcw_ddeeff"
    expect(entity_registry.async_get(entity_id).unique_id).to_equal(MAC_ADDRESS)
    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_ON)

    now = utcnow()
    bulb.async_update = AsyncMock(side_effect=RuntimeError)
    async_fire_time_changed(hass, now + timedelta(seconds=50))
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_UNAVAILABLE)
    bulb.async_update = AsyncMock()

    with _patch_discovery(), _patch_wifibulb():
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_DISCOVERY,
        )
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_ON)


@test.cases(
    test.case("full", discovery=FLUX_DISCOVERY, title=DEFAULT_ENTRY_TITLE),
    test.case("partial", discovery=FLUX_DISCOVERY_PARTIAL, title=DEFAULT_ENTRY_TITLE),
)
async def config_entry_fills_unique_id_with_directed_discovery(
    *,
    discovery: dict[str, str],
    title: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the unique id is added if its missing via directed (not broadcast) discovery."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS}, unique_id=None, title=IP_ADDRESS
    )
    config_entry.add_to_hass(hass)
    last_address = None

    async def _discovery(self: Any, *args: Any, address: Any = None, **kwargs: Any) -> Any:
        # Only return discovery results when doing directed discovery
        nonlocal last_address
        last_address = address
        return [discovery] if address == IP_ADDRESS else []

    def _mock_getBulbInfo(*args: Any, **kwargs: Any) -> Any:
        nonlocal last_address
        return [discovery] if last_address == IP_ADDRESS else []

    with (
        patch(
            "homeassistant.components.flux_led.discovery.AIOBulbScanner.async_scan",
            new=_discovery,
        ),
        patch(
            "homeassistant.components.flux_led.discovery.AIOBulbScanner.getBulbInfo",
            new=_mock_getBulbInfo,
        ),
        _patch_wifibulb(),
    ):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(config_entry.unique_id).to_equal(MAC_ADDRESS)
    expect(config_entry.title).to_equal(title)


@test
async def time_sync_startup_and_next_day(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that time is synced on startup and next day."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS}, unique_id=MAC_ADDRESS
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    with _patch_discovery(), _patch_wifibulb(device=bulb):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(len(bulb.async_set_time.mock_calls)).to_equal(1)

    with _patch_discovery(), _patch_wifibulb(device=bulb):
        async_fire_time_changed(hass, utcnow() + timedelta(hours=24))
        await hass.async_block_till_done()
    expect(len(bulb.async_set_time.mock_calls)).to_equal(2)


@test
async def unique_id_migrate_when_mac_discovered(
    _trigger: None = Depends(_trigger_executor),
    _translations: None = Depends(translations),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unique id migrated when mac discovered."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_REMOTE_ACCESS_HOST: "any",
            CONF_REMOTE_ACCESS_ENABLED: True,
            CONF_REMOTE_ACCESS_PORT: 1234,
            CONF_HOST: IP_ADDRESS,
            CONF_NAME: DEFAULT_ENTRY_TITLE,
        },
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    with _patch_discovery(no_device=True), _patch_wifibulb(device=bulb):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()

    expect(bool(config_entry.unique_id)).to_be(False)
    expect(entity_registry.async_get("light.bulb_rgbcw_ddeeff").unique_id).to_equal(
        config_entry.entry_id
    )
    expect(
        entity_registry.async_get("switch.bulb_rgbcw_ddeeff_remote_access").unique_id
    ).to_equal(f"{config_entry.entry_id}_remote_access")

    with _patch_discovery(), _patch_wifibulb(device=bulb):
        await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()

    expect(entity_registry.async_get("light.bulb_rgbcw_ddeeff").unique_id).to_equal(
        config_entry.unique_id
    )
    expect(
        entity_registry.async_get("switch.bulb_rgbcw_ddeeff_remote_access").unique_id
    ).to_equal(f"{config_entry.unique_id}_remote_access")


@test
async def unique_id_migrate_when_mac_discovered_via_discovery(
    _trigger: None = Depends(_trigger_executor),
    _translations: None = Depends(translations),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unique id migrated when mac discovered via discovery and the mac address from dhcp was one off."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_REMOTE_ACCESS_HOST: "any",
            CONF_REMOTE_ACCESS_ENABLED: True,
            CONF_REMOTE_ACCESS_PORT: 1234,
            CONF_HOST: IP_ADDRESS,
            CONF_NAME: DEFAULT_ENTRY_TITLE,
        },
        unique_id=MAC_ADDRESS_ONE_OFF,
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    with _patch_discovery(no_device=True), _patch_wifibulb(device=bulb):
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()

    expect(config_entry.unique_id).to_equal(MAC_ADDRESS_ONE_OFF)
    expect(entity_registry.async_get("light.bulb_rgbcw_ddeeff").unique_id).to_equal(
        MAC_ADDRESS_ONE_OFF
    )
    expect(
        entity_registry.async_get("switch.bulb_rgbcw_ddeeff_remote_access").unique_id
    ).to_equal(f"{MAC_ADDRESS_ONE_OFF}_remote_access")

    for _ in range(2):
        with _patch_discovery(), _patch_wifibulb(device=bulb):
            await hass.config_entries.async_reload(config_entry.entry_id)
            await hass.async_block_till_done()

        expect(
            entity_registry.async_get("light.bulb_rgbcw_ddeeff").unique_id
        ).to_equal(config_entry.unique_id)
        expect(
            entity_registry.async_get(
                "switch.bulb_rgbcw_ddeeff_remote_access"
            ).unique_id
        ).to_equal(f"{config_entry.unique_id}_remote_access")


@test
async def name_removed_when_it_matches_entry_title(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test name is removed when it matches the entry title."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_REMOTE_ACCESS_HOST: "any",
            CONF_REMOTE_ACCESS_ENABLED: True,
            CONF_REMOTE_ACCESS_PORT: 1234,
            CONF_HOST: IP_ADDRESS,
            CONF_NAME: DEFAULT_ENTRY_TITLE,
        },
        title=DEFAULT_ENTRY_TITLE,
    )
    config_entry.add_to_hass(hass)
    with _patch_discovery(), _patch_wifibulb():
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()
    expect(CONF_NAME not in config_entry.data).to_be(True)


@test
async def entry_is_reloaded_when_title_changes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the entry gets reloaded when the title changes."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_REMOTE_ACCESS_HOST: "any",
            CONF_REMOTE_ACCESS_ENABLED: True,
            CONF_REMOTE_ACCESS_PORT: 1234,
            CONF_HOST: IP_ADDRESS,
        },
        title=DEFAULT_ENTRY_TITLE,
    )
    config_entry.add_to_hass(hass)
    with _patch_discovery(), _patch_wifibulb():
        await async_setup_component(hass, flux_led.DOMAIN, {flux_led.DOMAIN: {}})
        await hass.async_block_till_done()

        hass.config_entries.async_update_entry(config_entry, title="Shop Light")
        expect(config_entry.title).to_equal("Shop Light")
        await hass.async_block_till_done()

    expect(
        hass.states.get("light.bulb_rgbcw_ddeeff").attributes[ATTR_FRIENDLY_NAME]
    ).to_equal("Shop Light")
