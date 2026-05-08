"""Test the Teslemetry init."""

from __future__ import annotations

from copy import deepcopy
import time
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientResponseError
from tesla_fleet_api.exceptions import (
    Forbidden,
    InvalidResponse,
    InvalidToken,
    RateLimited,
    SubscriptionRequired,
    TeslaFleetError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.teslemetry.const import CLIENT_ID, DOMAIN
from homeassistant.components.teslemetry.coordinator import (
    ENERGY_HISTORY_INTERVAL,
    ENERGY_INFO_INTERVAL,
    ENERGY_LIVE_INTERVAL,
    METADATA_INTERVAL,
    VEHICLE_INTERVAL,
)
from homeassistant.components.teslemetry.models import TeslemetryData
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ._fixtures import (
    mock_api_chain,
    mock_energy_history,
    mock_legacy,
    mock_live_status,
    mock_products,
    mock_site_info,
    mock_vehicle_data,
    setup_credentials,
)
from .common import setup_platform
from .const import (
    CONFIG_V1,
    ENERGY_HISTORY,
    LIVE_STATUS,
    METADATA,
    METADATA_NOSCOPE,
    PRODUCTS_MODERN,
    SITE_INFO,
    UNIQUE_ID,
    VEHICLE_DATA,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _creds: None = Depends(setup_credentials),
    _api: None = Depends(mock_api_chain),
) -> None:
    """Module-local fixture anchor that primes the network + OAuth + API mocks."""


@test
async def load_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test load and unload."""
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(isinstance(entry.runtime_data, TeslemetryData)).to_be(True)
    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(hasattr(entry, "runtime_data")).to_be(False)


@test.cases(
    test.case("invalid_token", side_effect=InvalidToken, state=ConfigEntryState.SETUP_ERROR),
    test.case(
        "subscription_required",
        side_effect=SubscriptionRequired,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "tesla_fleet_error", side_effect=TeslaFleetError, state=ConfigEntryState.SETUP_RETRY
    ),
)
async def init_error(
    *,
    side_effect: type[TeslaFleetError],
    state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    products: AsyncMock = Depends(mock_products),
) -> None:
    """Test init with errors."""
    products.side_effect = side_effect
    entry = await setup_platform(hass)
    expect(entry.state).to_be(state)


@test.skip("requires snapshot — port deferred")
async def devices() -> None:
    """Stub for test_devices (snapshot-based)."""


@test.cases(
    test.case("invalid_token", side_effect=InvalidToken, state=ConfigEntryState.SETUP_ERROR),
    test.case(
        "subscription_required",
        side_effect=SubscriptionRequired,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "tesla_fleet_error", side_effect=TeslaFleetError, state=ConfigEntryState.SETUP_RETRY
    ),
)
async def vehicle_refresh_error(
    *,
    side_effect: type[TeslaFleetError],
    state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    legacy: AsyncMock = Depends(mock_legacy),
) -> None:
    """Test coordinator refresh with an error."""
    vehicle_data.side_effect = side_effect
    entry = await setup_platform(hass)
    expect(entry.state).to_be(state)


@test.cases(
    test.case("invalid_token", side_effect=InvalidToken, state=ConfigEntryState.SETUP_ERROR),
    test.case(
        "subscription_required",
        side_effect=SubscriptionRequired,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "tesla_fleet_error", side_effect=TeslaFleetError, state=ConfigEntryState.SETUP_RETRY
    ),
)
async def energy_live_refresh_error(
    *,
    side_effect: type[TeslaFleetError],
    state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    live_status: AsyncMock = Depends(mock_live_status),
) -> None:
    """Test coordinator refresh with an error."""
    live_status.side_effect = side_effect
    entry = await setup_platform(hass)
    expect(entry.state).to_be(state)


@test.cases(
    test.case("invalid_token", side_effect=InvalidToken, state=ConfigEntryState.SETUP_ERROR),
    test.case(
        "subscription_required",
        side_effect=SubscriptionRequired,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "tesla_fleet_error", side_effect=TeslaFleetError, state=ConfigEntryState.SETUP_RETRY
    ),
)
async def energy_site_refresh_error(
    *,
    side_effect: type[TeslaFleetError],
    state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    site_info: AsyncMock = Depends(mock_site_info),
) -> None:
    """Test coordinator refresh with an error."""
    site_info.side_effect = side_effect
    entry = await setup_platform(hass)
    expect(entry.state).to_be(state)


@test.skip("requires snapshot + entity_registry_enabled_by_default")
async def vehicle_stream() -> None:
    """Stub for test_vehicle_stream (snapshot-based)."""


@test
async def no_live_status(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    live_status: AsyncMock = Depends(mock_live_status),
) -> None:
    """Test coordinator refresh handles a non-dict live_status response."""
    live_status.side_effect = AsyncMock({"response": ""})
    await setup_platform(hass)
    expect(hass.states.get("sensor.energy_site_grid_power")).to_be(None)


@test
async def modern_no_poll(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    products: AsyncMock = Depends(mock_products),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test that modern vehicles do not poll vehicle_data."""
    products.return_value = PRODUCTS_MODERN
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(vehicle_data.called).to_be(False)
    freezer.tick(VEHICLE_INTERVAL)
    expect(vehicle_data.called).to_be(False)
    freezer.tick(VEHICLE_INTERVAL)
    expect(vehicle_data.called).to_be(False)


@test
async def stale_device_removal(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    products: AsyncMock = Depends(mock_products),
) -> None:
    """Test removal of stale devices."""
    entry = await setup_platform(hass)

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "stale-vin")},
        manufacturer="Tesla",
        name="Stale Vehicle",
    )

    pre_devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    stale_identifiers = {
        identifier for device in pre_devices for identifier in device.identifiers
    }
    expect((DOMAIN, "stale-vin") in stale_identifiers).to_be(True)

    with patch(
        "tesla_fleet_api.teslemetry.Teslemetry.products",
        return_value={"response": []},
    ):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        post_devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
        post_identifiers = {
            identifier for device in post_devices for identifier in device.identifiers
        }
        expect((DOMAIN, "stale-vin") in post_identifiers).to_be(False)
        updated_device = device_registry.async_get_device(
            identifiers={(DOMAIN, "stale-vin")}
        )
        expect(updated_device).to_be(None)


@test
async def skipped_energy_site_is_removed_as_stale_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test skipped energy sites do not block stale device removal."""
    entry = await setup_platform(hass)

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "98765")},
        manufacturer="Tesla",
        name="Skipped Energy Site",
    )

    refreshed_metadata = deepcopy(METADATA)
    refreshed_metadata["energy_sites"]["98765"] = {
        "access": True,
        "name": "Skipped Energy Site",
    }

    with patch(
        "tesla_fleet_api.teslemetry.Teslemetry.metadata",
        return_value=refreshed_metadata,
    ):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    updated_device = device_registry.async_get_device(identifiers={(DOMAIN, "98765")})
    expect(updated_device).to_be(None)


@test
async def device_retention_during_reload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    products: AsyncMock = Depends(mock_products),
) -> None:
    """Test that valid devices are retained during a config entry reload."""
    entry = await setup_platform(hass)

    pre_devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    pre_count = len(pre_devices)
    pre_identifiers = {
        identifier for device in pre_devices for identifier in device.identifiers
    }

    expect(pre_count > 0).to_be(True)
    original_identifiers = pre_identifiers.copy()

    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    post_devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    post_count = len(post_devices)
    post_identifiers = {
        identifier for device in post_devices for identifier in device.identifiers
    }
    expect(post_count).to_equal(pre_count)
    expect(post_identifiers).to_equal(original_identifiers)


@test
async def migrate_from_version_1_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful config migration from version 1."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        unique_id=UNIQUE_ID,
        data=CONFIG_V1,
    )

    with patch(
        "homeassistant.components.teslemetry.Teslemetry.migrate_to_oauth",
        new_callable=AsyncMock,
    ) as mock_migrate:
        mock_migrate.return_value = {
            "token": {
                "access_token": "migrated_token",
                "token_type": "Bearer",
                "refresh_token": "migrated_refresh_token",
                "expires_in": 3600,
                "expires_at": time.time() + 3600,
            }
        }

        mock_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        mock_migrate.assert_called_once_with(CLIENT_ID, hass.config.location_name)

    expect(mock_entry.version).to_equal(2)
    expect("token" in mock_entry.data).to_be(True)
    expect(mock_entry.data["token"]["access_token"]).to_equal("migrated_token")
    expect(mock_entry.data["token"]["refresh_token"]).to_equal("migrated_refresh_token")
    expect(mock_entry.data["auth_implementation"]).to_equal(DOMAIN)
    expect(mock_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def migrate_from_version_1_token_endpoint_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config migration handles token endpoint errors."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        unique_id=UNIQUE_ID,
        data=CONFIG_V1,
    )

    with patch(
        "homeassistant.components.teslemetry.Teslemetry.migrate_to_oauth",
        new_callable=AsyncMock,
    ) as mock_migrate:
        mock_migrate.side_effect = ClientResponseError(
            request_info=MagicMock(), history=(), status=400
        )
        mock_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        mock_migrate.assert_called_once_with(CLIENT_ID, hass.config.location_name)

    entry = hass.config_entries.async_get_entry(mock_entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
    expect(entry.version).to_equal(1)


@test
async def migrate_version_2_no_migration_needed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that version 2 entries don't need migration."""
    oauth_config = {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": "existing_oauth_token",
            "token_type": "Bearer",
            "refresh_token": "existing_refresh_token",
            "expires_in": 3600,
            "expires_at": 1234567890,
        },
    }

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=UNIQUE_ID,
        data=oauth_config,
    )

    with patch(
        "homeassistant.components.teslemetry.Teslemetry.migrate_to_oauth",
        new_callable=AsyncMock,
    ) as mock_migrate:
        mock_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()
        mock_migrate.assert_not_called()

    entry = hass.config_entries.async_get_entry(mock_entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.version).to_equal(2)
    expect(entry.data).to_equal(oauth_config)
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def migrate_from_future_version_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migration fails for future versions."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        unique_id=UNIQUE_ID,
        data={
            "token": {
                "access_token": "future_token",
                "token_type": "Bearer",
                "refresh_token": "future_refresh_token",
                "expires_in": 3600,
            }
        },
    )

    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    entry = hass.config_entries.async_get_entry(mock_entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
    expect(entry.version).to_equal(3)


@test
async def oauth_implementation_not_available(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that missing OAuth implementation triggers reauth."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=UNIQUE_ID,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_at": int(time.time()) + 3600,
            },
        },
    )
    mock_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.teslemetry.async_get_config_entry_implementation",
        side_effect=ValueError("Implementation not available"),
    ):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

    entry = hass.config_entries.async_get_entry(mock_entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test.cases(
    test.case("rate_limited", exception=RateLimited(data={"after": 5}), expected_retry_after=5.0),
    test.case("invalid_response", exception=InvalidResponse(), expected_retry_after=10.0),
)
async def site_info_retry_exceptions(
    *,
    exception: TeslaFleetError,
    expected_retry_after: float,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    site_info: AsyncMock = Depends(mock_site_info),
) -> None:
    """Test UpdateFailed with retry_after for site info coordinator."""
    site_info.side_effect = exception
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(site_info.call_count).to_equal(1)


@test.cases(
    test.case("rate_limited", exception=RateLimited(data={"after": 5}), expected_retry_after=5.0),
    test.case("invalid_response", exception=InvalidResponse(), expected_retry_after=10.0),
)
async def vehicle_data_retry_exceptions(
    *,
    exception: TeslaFleetError,
    expected_retry_after: float,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    legacy: AsyncMock = Depends(mock_legacy),
) -> None:
    """Test UpdateFailed with retry_after for vehicle data coordinator."""
    vehicle_data.side_effect = exception
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(vehicle_data.call_count).to_equal(1)


@test.cases(
    test.case("rate_limited", exception=RateLimited(data={"after": 5}), expected_retry_after=5.0),
    test.case("invalid_response", exception=InvalidResponse(), expected_retry_after=10.0),
)
async def live_status_coordinator_retry_exceptions(
    *,
    exception: TeslaFleetError,
    expected_retry_after: float,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
    live_status: AsyncMock = Depends(mock_live_status),
) -> None:
    """Test live status coordinator raises UpdateFailed with retry_after."""
    call_count = 0

    def live_status_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return deepcopy(LIVE_STATUS)
        if call_count == 2:
            raise exception
        return deepcopy(LIVE_STATUS)

    live_status.side_effect = live_status_side_effect

    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(call_count).to_equal(1)

    freezer.tick(ENERGY_LIVE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(call_count).to_equal(2)
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test.cases(
    test.case("rate_limited", exception=RateLimited(data={"after": 5}), expected_retry_after=5.0),
    test.case("invalid_response", exception=InvalidResponse(), expected_retry_after=10.0),
)
async def energy_history_coordinator_retry_exceptions(
    *,
    exception: TeslaFleetError,
    expected_retry_after: float,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
    energy_history: AsyncMock = Depends(mock_energy_history),
) -> None:
    """Test energy history coordinator raises UpdateFailed with retry_after."""
    call_count = 0

    def energy_history_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise exception
        return ENERGY_HISTORY

    energy_history.side_effect = energy_history_side_effect

    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(call_count).to_equal(0)

    freezer.tick(ENERGY_HISTORY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(call_count).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def live_status_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test live status coordinator handles auth errors."""
    call_count = 0

    def live_status_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return deepcopy(LIVE_STATUS)
        raise InvalidToken

    with patch(
        "tesla_fleet_api.tesla.energysite.EnergySite.live_status",
        side_effect=live_status_side_effect,
    ):
        entry = await setup_platform(hass)
        expect(entry.state).to_be(ConfigEntryState.LOADED)

        freezer.tick(ENERGY_LIVE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def live_status_generic_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test live status coordinator handles generic TeslaFleetError."""
    call_count = 0

    def live_status_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return deepcopy(LIVE_STATUS)
        raise TeslaFleetError

    with patch(
        "tesla_fleet_api.tesla.energysite.EnergySite.live_status",
        side_effect=live_status_side_effect,
    ):
        entry = await setup_platform(hass)
        expect(entry.state).to_be(ConfigEntryState.LOADED)

        freezer.tick(ENERGY_LIVE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def missing_token_data(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that missing token data in config entry triggers auth failure."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=UNIQUE_ID,
        data={
            "auth_implementation": DOMAIN,
        },
    )
    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    entry = hass.config_entries.async_get_entry(mock_entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def vehicle_streaming_version_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test vehicle sw_version is updated when streaming reports new version."""
    version_listeners: list = []

    def mock_listen_version(callback):
        version_listeners.append(callback)
        return lambda: None

    with patch(
        "teslemetry_stream.TeslemetryStreamVehicle.listen_Version",
        side_effect=mock_listen_version,
    ):
        entry = await setup_platform(hass)
        expect(entry.state).to_be(ConfigEntryState.LOADED)

    vin = "LRW3F7EK4NC700000"
    device = device_registry.async_get_device(identifiers={(DOMAIN, vin)})
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_equal("2026.0.0")

    expect(len(version_listeners) > 0).to_be(True)
    version_listeners[0]("2026.1.0 abc123")
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, vin)})
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_equal("2026.1.0")


@test
async def vehicle_streaming_version_update_ignores_none(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test vehicle sw_version is not updated when streaming reports None."""
    version_listeners: list = []

    def mock_listen_version(callback):
        version_listeners.append(callback)
        return lambda: None

    with patch(
        "teslemetry_stream.TeslemetryStreamVehicle.listen_Version",
        side_effect=mock_listen_version,
    ):
        entry = await setup_platform(hass)
        expect(entry.state).to_be(ConfigEntryState.LOADED)

    vin = "LRW3F7EK4NC700000"
    device = device_registry.async_get_device(identifiers={(DOMAIN, vin)})
    expect(device is not None).to_be(True)
    original_version = device.sw_version

    expect(len(version_listeners) > 0).to_be(True)
    version_listeners[0](None)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, vin)})
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_equal(original_version)


@test
async def vehicle_polling_version_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    legacy: AsyncMock = Depends(mock_legacy),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test vehicle sw_version is updated when polling coordinator receives new version."""
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    vin = "LRW3F7EK4NC700000"
    device = device_registry.async_get_device(identifiers={(DOMAIN, vin)})
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_equal("2026.0.0")

    updated_vehicle_data = deepcopy(VEHICLE_DATA)
    updated_vehicle_data["response"]["vehicle_state"]["car_version"] = "2026.2.0 def456"
    vehicle_data.return_value = updated_vehicle_data

    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, vin)})
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_equal("2026.2.0")


@test
async def energy_site_version_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    site_info: AsyncMock = Depends(mock_site_info),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test energy site sw_version is updated when info coordinator receives new version."""
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    site_id = "123456"
    device = device_registry.async_get_device(identifiers={(DOMAIN, site_id)})
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_equal("23.44.0 eb113390")

    updated_site_info = deepcopy(SITE_INFO)
    updated_site_info["response"]["version"] = "24.1.0 abc123"
    site_info.side_effect = lambda: updated_site_info

    freezer.tick(ENERGY_INFO_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, site_id)})
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_equal("24.1.0 abc123")


@test
async def live_status_auth_failed_forbidden(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    live_status: AsyncMock = Depends(mock_live_status),
) -> None:
    """Test Forbidden exception during live_status triggers auth failure."""
    live_status.side_effect = Forbidden
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test.cases(
    test.case("live_then_error", side_effect=[deepcopy(LIVE_STATUS), TeslaFleetError]),
)
async def live_status_coordinator_refresh_error(
    *,
    side_effect: list,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
    live_status: AsyncMock = Depends(mock_live_status),
) -> None:
    """Test live status coordinator handles errors during refresh."""
    live_status.side_effect = side_effect

    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    freezer.tick(ENERGY_LIVE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test.cases(
    test.case("invalid_token", side_effect=[InvalidToken]),
    test.case("tesla_fleet_error", side_effect=[TeslaFleetError]),
    test.case("history_then_empty", side_effect=[ENERGY_HISTORY, {"response": {}}]),
)
async def energy_history_coordinator_refresh_errors(
    *,
    side_effect: list,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
    energy_history: AsyncMock = Depends(mock_energy_history),
) -> None:
    """Test energy history coordinator handles errors during refresh."""
    energy_history.side_effect = side_effect

    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    freezer.tick(ENERGY_HISTORY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def dynamic_device_discovery_triggers_reload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test that metadata coordinator triggers reload when new vehicle is added."""
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    new_metadata = deepcopy(METADATA)
    new_metadata["vehicles"]["5YJ3E1EA1NF000001"] = {
        "proxy": True,
        "access": True,
        "polling": False,
        "firmware": "2026.0.0",
    }

    with (
        patch(
            "tesla_fleet_api.teslemetry.Teslemetry.metadata",
            return_value=new_metadata,
        ),
        patch.object(hass.config_entries, "async_schedule_reload") as mock_reload,
    ):
        freezer.tick(METADATA_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    mock_reload.assert_called_once_with(entry.entry_id)


@test
async def dynamic_device_discovery_no_reload_for_scope_only_change(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test metadata refresh does not reload when only scopes change."""
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    with (
        patch(
            "tesla_fleet_api.teslemetry.Teslemetry.metadata",
            return_value=deepcopy(METADATA_NOSCOPE),
        ),
        patch.object(hass.config_entries, "async_schedule_reload") as mock_reload,
    ):
        freezer.tick(METADATA_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    mock_reload.assert_not_called()


@test
async def dynamic_device_discovery_no_reload_without_changes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test that metadata coordinator refresh without changes does not reload."""
    entry = await setup_platform(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    with (
        patch(
            "tesla_fleet_api.teslemetry.Teslemetry.metadata",
            return_value=deepcopy(METADATA),
        ),
        patch.object(hass.config_entries, "async_schedule_reload") as mock_reload,
    ):
        freezer.tick(METADATA_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    mock_reload.assert_not_called()
