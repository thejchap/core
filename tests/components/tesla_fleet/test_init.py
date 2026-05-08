"""Test the Tesla Fleet init."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from unittest.mock import AsyncMock, Mock, patch

from tesla_fleet_api.const import Scope, VehicleDataEndpoint
from tesla_fleet_api.exceptions import (
    InvalidRegion,
    InvalidToken,
    LibraryError,
    LoginRequired,
    OAuthExpired,
    RateLimited,
    TeslaFleetError,
    VehicleOffline,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.tesla_fleet.const import DOMAIN, SCOPES
from homeassistant.components.tesla_fleet.coordinator import (
    ENERGY_HISTORY_INTERVAL,
    ENERGY_INTERVAL,
    ENERGY_INTERVAL_SECONDS,
    VEHICLE_INTERVAL,
    VEHICLE_INTERVAL_SECONDS,
    VEHICLE_WAIT,
    _invalidate_access_token,
)
from homeassistant.components.tesla_fleet.models import TeslaFleetData
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import (
    OAuth2TokenRequestReauthError,
    OAuth2TokenRequestTransientError,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)

from ._fixtures import (
    bad_config_entry,
    expires_at,
    mock_api_chain,
    mock_energy_history,
    mock_find_server,
    mock_live_status,
    mock_products,
    mock_site_info,
    mock_vehicle_data,
    mock_vehicle_state,
    noscope_config_entry,
    normal_config_entry,
)
from .common import (
    ENERGY_SITE_ID,
    VIN,
    create_config_entry,
    get_state_by_unique_id,
    setup_platform,
)
from .const import LIVE_STATUS, VEHICLE_ASLEEP, VEHICLE_DATA_ALT

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)

RUNTIME_ERRORS = [InvalidToken, OAuthExpired, LoginRequired, TeslaFleetError]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _api: None = Depends(mock_api_chain),
) -> None:
    """Module-local fixture anchor that primes the network + API mocks."""


@test
async def load_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
) -> None:
    """Test load and unload."""
    await setup_platform(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(isinstance(entry.runtime_data, TeslaFleetData)).to_be(True)
    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(hasattr(entry, "runtime_data")).to_be(False)


@test.cases(
    test.case("invalid_token", side_effect=InvalidToken, state=ConfigEntryState.SETUP_ERROR),
    test.case("oauth_expired", side_effect=OAuthExpired, state=ConfigEntryState.SETUP_ERROR),
    test.case("login_required", side_effect=LoginRequired, state=ConfigEntryState.SETUP_ERROR),
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
    entry: MockConfigEntry = Depends(normal_config_entry),
    products: AsyncMock = Depends(mock_products),
) -> None:
    """Test init with errors."""
    products.side_effect = side_effect
    await setup_platform(hass, entry)
    expect(entry.state).to_be(state)


@test
async def oauth_refresh_expired(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    products: AsyncMock = Depends(mock_products),
) -> None:
    """Test init with expired Oauth token."""
    with patch(
        "homeassistant.components.tesla_fleet.OAuth2Session.async_ensure_token_valid",
        side_effect=OAuth2TokenRequestReauthError(
            domain=DOMAIN,
            request_info=Mock(),
        ),
    ) as mock_async_ensure_token_valid:
        products.side_effect = InvalidRegion
        await setup_platform(hass, entry)
        mock_async_ensure_token_valid.assert_called_once()
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def oauth_refresh_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    products: AsyncMock = Depends(mock_products),
) -> None:
    """Test init with Oauth refresh failure."""
    with patch(
        "homeassistant.components.tesla_fleet.OAuth2Session.async_ensure_token_valid",
        side_effect=OAuth2TokenRequestTransientError(
            domain=DOMAIN,
            request_info=Mock(),
        ),
    ) as mock_async_ensure_token_valid:
        products.side_effect = InvalidRegion
        await setup_platform(hass, entry)
        mock_async_ensure_token_valid.assert_called_once()
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_uses_scopes_from_refreshed_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(noscope_config_entry),
) -> None:
    """Test setup uses scopes from the refreshed OAuth token."""
    refreshed_token = create_config_entry(
        expires_at=3600,
        scopes=SCOPES,
    ).data[CONF_TOKEN]

    entry.data[CONF_TOKEN]["expires_at"] = 0

    with patch(
        "homeassistant.components.tesla_fleet.oauth.TeslaUserImplementation.async_refresh_token",
        return_value=refreshed_token,
    ) as mock_async_refresh_token:
        await setup_platform(hass, entry)

    mock_async_refresh_token.assert_awaited_once()
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry.runtime_data.scopes).to_equal(SCOPES)
    expect(bool(entry.runtime_data.vehicles)).to_be(True)


@test
async def invalidate_access_token_updates_when_not_expired(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
) -> None:
    """Test invalidating token updates entry when token is not expired."""
    entry.add_to_hass(hass)
    expected_data = {
        **dict(entry.data),
        CONF_TOKEN: {
            **entry.data[CONF_TOKEN],
            "expires_at": 0,
        },
    }

    _invalidate_access_token(hass, entry)

    expect(dict(entry.data)).to_equal(expected_data)


@test
async def invalidate_access_token_noop_when_already_expired(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
) -> None:
    """Test invalidating token does not update an already expired token."""
    entry.add_to_hass(hass)
    entry.data[CONF_TOKEN]["expires_at"] = 0
    before_data = dict(entry.data)

    _invalidate_access_token(hass, entry)

    expect(dict(entry.data)).to_equal(before_data)


@test
async def invalidate_access_token_noop_when_token_missing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalidating token does not update when token data is missing."""
    missing_token_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"auth_implementation": DOMAIN},
    )
    missing_token_entry.add_to_hass(hass)
    before_data = dict(missing_token_entry.data)

    _invalidate_access_token(hass, missing_token_entry)

    expect(dict(missing_token_entry.data)).to_equal(before_data)


@test.skip("requires snapshot — port deferred")
async def devices() -> None:
    """Stub for test_devices (snapshot-based)."""


@test
async def vehicle_refresh_offline(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    vehicle_state: AsyncMock = Depends(mock_vehicle_state),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator refresh with offline vehicle."""
    await setup_platform(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    vehicle_state.assert_called_once()
    vehicle_data.assert_called_once()
    vehicle_state.reset_mock()
    vehicle_data.reset_mock()

    vehicle_data.side_effect = VehicleOffline
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    vehicle_state.assert_called_once()
    vehicle_data.assert_called_once()
    vehicle_state.reset_mock()
    vehicle_data.reset_mock()

    vehicle_state.return_value = VEHICLE_ASLEEP
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    vehicle_state.assert_called_once()
    vehicle_data.assert_not_called()


@test.cases(
    test.case("invalid_token", side_effect=InvalidToken),
    test.case("oauth_expired", side_effect=OAuthExpired),
    test.case("login_required", side_effect=LoginRequired),
    test.case("tesla_fleet_error", side_effect=TeslaFleetError),
)
async def vehicle_refresh_error(
    *,
    side_effect: type[TeslaFleetError],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator refresh makes entity unavailable."""
    await setup_platform(hass, entry)

    vehicle_data.side_effect = side_effect
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = get_state_by_unique_id(hass, "sensor", f"{VIN}-charge_state_battery_level")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("unavailable")


@test
async def vehicle_refresh_token_expired_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator recovers from expired vehicle access token."""
    await setup_platform(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    state = get_state_by_unique_id(hass, "sensor", f"{VIN}-charge_state_battery_level")
    expect(state is not None).to_be(True)
    expect(state.state != "unavailable").to_be(True)

    vehicle_data.reset_mock()
    vehicle_data.side_effect = OAuthExpired

    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    state = get_state_by_unique_id(hass, "sensor", f"{VIN}-charge_state_battery_level")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("unavailable")
    expect(entry.data["token"]["expires_at"]).to_equal(0)
    expect(vehicle_data.call_count).to_equal(1)

    vehicle_data.side_effect = None
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = get_state_by_unique_id(hass, "sensor", f"{VIN}-charge_state_battery_level")
    expect(state is not None).to_be(True)
    expect(state.state != "unavailable").to_be(True)
    expect(vehicle_data.call_count).to_equal(2)


@test
async def vehicle_refresh_ratelimited(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator refresh handles 429."""
    vehicle_data.side_effect = RateLimited({"after": VEHICLE_INTERVAL_SECONDS + 10})
    await setup_platform(hass, entry)

    state = get_state_by_unique_id(hass, "sensor", f"{VIN}-charge_state_battery_level")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("unknown")

    vehicle_data.reset_mock()
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = get_state_by_unique_id(hass, "sensor", f"{VIN}-charge_state_battery_level")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("unknown")


@test
async def vehicle_refresh_ratelimited_no_after(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator refresh handles 429 without after."""
    await setup_platform(hass, entry)
    expect(vehicle_data.call_count).to_equal(1)

    vehicle_data.side_effect = RateLimited({})
    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(vehicle_data.call_count).to_equal(2)

    freezer.tick(VEHICLE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(vehicle_data.call_count).to_equal(3)


@test
async def init_invalid_region(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    expires_at_value: int = Depends(expires_at),
) -> None:
    """Test init with an invalid region in the token."""
    config_entry = create_config_entry(
        expires_at_value, [Scope.VEHICLE_DEVICE_DATA], region="other"
    )

    with patch("homeassistant.components.tesla_fleet.TeslaFleetApi") as mock_api:
        await setup_platform(hass, config_entry)
        mock_api.assert_called()
        expect(mock_api.call_args.kwargs.get("region")).to_be(None)


@test
async def vehicle_sleep(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator vehicle sleep behavior."""
    TEST_INTERVAL = timedelta(seconds=120)

    with patch(
        "homeassistant.components.tesla_fleet.coordinator.VEHICLE_INTERVAL",
        TEST_INTERVAL,
    ):
        await setup_platform(hass, entry)
        expect(vehicle_data.call_count).to_equal(1)

        freezer.tick(VEHICLE_WAIT + TEST_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(vehicle_data.call_count).to_equal(2)

        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(vehicle_data.call_count).to_equal(2)

        freezer.tick(VEHICLE_WAIT)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(vehicle_data.call_count).to_equal(3)

        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(vehicle_data.call_count).to_equal(4)

        vehicle_data.return_value = VEHICLE_DATA_ALT
        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(vehicle_data.call_count).to_equal(5)

        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(vehicle_data.call_count).to_equal(6)

        freezer.tick(TEST_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(vehicle_data.call_count).to_equal(7)


@test.cases(
    test.case("invalid_token", side_effect=InvalidToken),
    test.case("oauth_expired", side_effect=OAuthExpired),
    test.case("login_required", side_effect=LoginRequired),
    test.case("tesla_fleet_error", side_effect=TeslaFleetError),
)
async def energy_live_refresh_error(
    *,
    side_effect: type[TeslaFleetError],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    live_status: AsyncMock = Depends(mock_live_status),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test energy live coordinator refresh with an error."""
    await setup_platform(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    live_status.side_effect = side_effect
    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = get_state_by_unique_id(hass, "sensor", f"{ENERGY_SITE_ID}-grid_power")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("unavailable")


@test
async def energy_live_refresh_bad_response(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    live_status: AsyncMock = Depends(mock_live_status),
) -> None:
    """Test coordinator refresh with malformed live status payload."""
    bad_live_status = deepcopy(LIVE_STATUS)
    bad_live_status["response"] = "site data is unavailable"
    live_status.side_effect = None
    live_status.return_value = bad_live_status

    await setup_platform(hass, entry)

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    state = get_state_by_unique_id(hass, "sensor", f"{VIN}-charge_state_battery_level")
    expect(state is not None).to_be(True)
    expect(state.state != "unavailable").to_be(True)


@test
async def energy_live_refresh_bad_wall_connectors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    live_status: AsyncMock = Depends(mock_live_status),
) -> None:
    """Test coordinator refresh with malformed wall connector payload."""
    bad_live_status = deepcopy(LIVE_STATUS)
    bad_live_status["response"]["wall_connectors"] = "site data is unavailable"
    live_status.side_effect = None
    live_status.return_value = bad_live_status

    await setup_platform(hass, entry)

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    state = get_state_by_unique_id(hass, "sensor", f"{VIN}-charge_state_battery_level")
    expect(state is not None).to_be(True)
    expect(state.state != "unavailable").to_be(True)


@test.cases(
    test.case("invalid_token", side_effect=InvalidToken),
    test.case("oauth_expired", side_effect=OAuthExpired),
    test.case("login_required", side_effect=LoginRequired),
    test.case("tesla_fleet_error", side_effect=TeslaFleetError),
)
async def energy_site_refresh_error(
    *,
    side_effect: type[TeslaFleetError],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    site_info: AsyncMock = Depends(mock_site_info),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test energy site coordinator refresh with an error."""
    await setup_platform(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    site_info.side_effect = side_effect
    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = get_state_by_unique_id(hass, "number", f"{ENERGY_SITE_ID}-backup_reserve_percent")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("unavailable")


@test
async def energy_refresh_token_expired_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    live_status: AsyncMock = Depends(mock_live_status),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test energy coordinator recovers from expired access token."""
    await setup_platform(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    state = get_state_by_unique_id(hass, "sensor", f"{ENERGY_SITE_ID}-grid_power")
    expect(state is not None).to_be(True)
    expect(state.state != "unavailable").to_be(True)

    live_status.reset_mock()
    live_status.side_effect = OAuthExpired

    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    state = get_state_by_unique_id(hass, "sensor", f"{ENERGY_SITE_ID}-grid_power")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("unavailable")
    expect(entry.data["token"]["expires_at"]).to_equal(0)
    expect(live_status.call_count).to_equal(1)

    live_status.side_effect = None
    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = get_state_by_unique_id(hass, "sensor", f"{ENERGY_SITE_ID}-grid_power")
    expect(state is not None).to_be(True)
    expect(state.state != "unavailable").to_be(True)
    expect(live_status.call_count).to_equal(2)


@test.cases(
    test.case("invalid_token", side_effect=InvalidToken),
    test.case("oauth_expired", side_effect=OAuthExpired),
    test.case("login_required", side_effect=LoginRequired),
    test.case("tesla_fleet_error", side_effect=TeslaFleetError),
)
async def energy_history_refresh_error(
    *,
    side_effect: type[TeslaFleetError],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    energy_history: AsyncMock = Depends(mock_energy_history),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test energy history coordinator refresh with an error."""
    await setup_platform(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    energy_history.side_effect = side_effect
    freezer.tick(ENERGY_HISTORY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def energy_live_refresh_ratelimited(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    live_status: AsyncMock = Depends(mock_live_status),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test energy live coordinator refresh handles 429."""
    await setup_platform(hass, entry)

    live_status.side_effect = RateLimited({"after": ENERGY_INTERVAL_SECONDS + 10})
    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(live_status.call_count).to_equal(2)

    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(live_status.call_count).to_equal(2)

    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(live_status.call_count).to_equal(3)


@test
async def energy_info_refresh_ratelimited(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    site_info: AsyncMock = Depends(mock_site_info),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test energy info coordinator refresh handles 429."""
    await setup_platform(hass, entry)

    site_info.side_effect = RateLimited({"after": ENERGY_INTERVAL_SECONDS + 10})
    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(site_info.call_count).to_equal(2)

    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(site_info.call_count).to_equal(2)

    freezer.tick(ENERGY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(site_info.call_count).to_equal(3)


@test
async def energy_history_refresh_ratelimited(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    energy_history: AsyncMock = Depends(mock_energy_history),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test energy history coordinator refresh handles 429."""
    await setup_platform(hass, entry)

    energy_history.side_effect = RateLimited(
        {"after": int(ENERGY_HISTORY_INTERVAL.total_seconds() + 10)}
    )
    freezer.tick(ENERGY_HISTORY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(energy_history.call_count).to_equal(1)

    freezer.tick(ENERGY_HISTORY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(energy_history.call_count).to_equal(1)

    freezer.tick(ENERGY_HISTORY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(energy_history.call_count).to_equal(2)


@test
async def init_region_issue(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    products: AsyncMock = Depends(mock_products),
    find_server: AsyncMock = Depends(mock_find_server),
) -> None:
    """Test init with region issue."""
    products.side_effect = InvalidRegion
    await setup_platform(hass, entry)
    find_server.assert_called_once()
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def init_region_issue_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    products: AsyncMock = Depends(mock_products),
    find_server: AsyncMock = Depends(mock_find_server),
) -> None:
    """Test init with unresolvable region issue."""
    products.side_effect = InvalidRegion
    find_server.side_effect = LibraryError
    await setup_platform(hass, entry)
    find_server.assert_called_once()
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def signing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    products: AsyncMock = Depends(mock_products),
) -> None:
    """Tests when a vehicle requires signing."""
    products_data = deepcopy(products.return_value)
    products_data["response"][0]["command_signing"] = "required"
    products.return_value = products_data

    with patch(
        "homeassistant.components.tesla_fleet.TeslaFleetApi.get_private_key"
    ) as mock_get_private_key:
        await setup_platform(hass, entry)
        mock_get_private_key.assert_called_once()


@test
async def bad_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(bad_config_entry),
) -> None:
    """Test handling of a bad authentication implementation."""
    await setup_platform(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    expect(any(entry.async_get_active_flows(hass, {"reauth"}))).to_be(True)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(bool(result["errors"])).to_be(False)


@test
async def vehicle_without_location_scope(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    expires_at_value: int = Depends(expires_at),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
) -> None:
    """Test vehicle setup without VEHICLE_LOCATION scope excludes location endpoint."""
    config_entry = create_config_entry(
        expires_at_value,
        [
            Scope.OPENID,
            Scope.OFFLINE_ACCESS,
            Scope.VEHICLE_DEVICE_DATA,
        ],
    )

    await setup_platform(hass, config_entry)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    vehicle_data.assert_called()
    call_args = vehicle_data.call_args
    endpoints = call_args.kwargs.get("endpoints", [])

    expect(VehicleDataEndpoint.LOCATION_DATA in endpoints).to_be(False)
    expect(VehicleDataEndpoint.CHARGE_STATE in endpoints).to_be(True)
    expect(VehicleDataEndpoint.CLIMATE_STATE in endpoints).to_be(True)
    expect(VehicleDataEndpoint.DRIVE_STATE in endpoints).to_be(True)
    expect(VehicleDataEndpoint.VEHICLE_STATE in endpoints).to_be(True)
    expect(VehicleDataEndpoint.VEHICLE_CONFIG in endpoints).to_be(True)


@test
async def vehicle_with_location_scope(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
    vehicle_data: AsyncMock = Depends(mock_vehicle_data),
) -> None:
    """Test vehicle setup with VEHICLE_LOCATION scope includes location endpoint."""
    await setup_platform(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    vehicle_data.assert_called()
    call_args = vehicle_data.call_args
    endpoints = call_args.kwargs.get("endpoints", [])

    expect(VehicleDataEndpoint.LOCATION_DATA in endpoints).to_be(True)
    expect(VehicleDataEndpoint.CHARGE_STATE in endpoints).to_be(True)
    expect(VehicleDataEndpoint.CLIMATE_STATE in endpoints).to_be(True)
    expect(VehicleDataEndpoint.DRIVE_STATE in endpoints).to_be(True)
    expect(VehicleDataEndpoint.VEHICLE_STATE in endpoints).to_be(True)
    expect(VehicleDataEndpoint.VEHICLE_CONFIG in endpoints).to_be(True)


@test
async def oauth_implementation_not_available(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(normal_config_entry),
) -> None:
    """Test that unavailable OAuth implementation raises ConfigEntryNotReady."""
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.tesla_fleet.async_get_config_entry_implementation",
        side_effect=ImplementationUnavailableError,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
