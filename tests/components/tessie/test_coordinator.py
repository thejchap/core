"""Test the Tessie sensor platform."""

from copy import deepcopy
from datetime import timedelta
from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
from tesla_fleet_api.exceptions import Forbidden, InvalidToken, MissingToken
from tryke import Depends, expect, fixture, test

from homeassistant.components.tessie import PLATFORMS
from homeassistant.components.tessie.const import DOMAIN
from homeassistant.components.tessie.coordinator import (
    TESSIE_ENERGY_HISTORY_INTERVAL,
    TESSIE_FLEET_API_SYNC_INTERVAL,
    TESSIE_SYNC_INTERVAL,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation as translation_helper
from homeassistant.helpers.update_coordinator import UpdateFailed

from ._fixtures import (
    mock_energy_history,
    mock_get_state,
    mock_get_state_of_all_vehicles,
    mock_live_status,
    mock_products,
    mock_request,
    mock_scopes,
    mock_site_info,
)
from .common import (
    ENERGY_HISTORY,
    ERROR_AUTH,
    ERROR_CONNECTION,
    ERROR_UNKNOWN,
    setup_platform,
)

from tests.common import async_fire_time_changed
from tests.hass_fixtures import freezer as freezer_fx, hass as hass_fx, mock_network

WAIT = timedelta(seconds=TESSIE_SYNC_INTERVAL)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _gs: AsyncMock = Depends(mock_get_state),
    _gsv: AsyncMock = Depends(mock_get_state_of_all_vehicles),
    _ms: AsyncMock = Depends(mock_scopes),
    _mp: AsyncMock = Depends(mock_products),
    _mr: AsyncMock = Depends(mock_request),
    _mls: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    _meh: AsyncMock = Depends(mock_energy_history),
) -> int:
    """Apply autouse mocks via this trigger fixture."""
    return 0


def _load_translations(hass: HomeAssistant) -> None:
    """Preload tessie strings.json into the translation cache.

    The dev tree lacks ``translations/en.json`` files, so the real translation
    loader returns no entity data. Read ``strings.json`` directly and seed the
    cache so entity_ids resolve via ``translation_key`` (e.g. ``binary_sensor.test_status``).
    """
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    strings_path = (
        Path(__file__).resolve().parents[3]
        / "homeassistant"
        / "components"
        / DOMAIN
        / "strings.json"
    )
    data: dict = json.loads(strings_path.read_text())
    cache = translation_helper._async_get_translations_cache(hass)
    translation_data = {"en": {DOMAIN: data}}
    cache._build_category_cache("en", {DOMAIN}, translation_data["en"])
    cache.cache_data.loaded.setdefault("en", set()).add(DOMAIN)


@test
async def coordinator_online(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_get_state: AsyncMock = Depends(mock_get_state),
    _mls: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    _meh: AsyncMock = Depends(mock_energy_history),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Tests that the coordinator handles online vehicles."""
    _load_translations(hass)

    await setup_platform(hass, PLATFORMS)

    freezer.tick(WAIT)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_get_state.assert_called_once()
    expect(hass.states.get("binary_sensor.test_status").state).to_equal(STATE_ON)


@test
async def coordinator_clienterror(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_get_state: AsyncMock = Depends(mock_get_state),
    _mls: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    _meh: AsyncMock = Depends(mock_energy_history),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Tests that the coordinator handles client errors."""
    mock_get_state.side_effect = ERROR_UNKNOWN
    _load_translations(hass)

    entry = await setup_platform(hass, [Platform.BINARY_SENSOR])
    coordinator = entry.runtime_data.vehicles[0].data_coordinator

    freezer.tick(WAIT)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_get_state.assert_called_once()
    expect(hass.states.get("binary_sensor.test_status").state).to_equal(
        STATE_UNAVAILABLE
    )
    expect(isinstance(coordinator.last_exception, UpdateFailed)).to_be(True)
    expect(coordinator.last_exception.translation_domain).to_equal(DOMAIN)
    expect(coordinator.last_exception.translation_key).to_equal("cannot_connect")


@test
async def coordinator_auth(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_get_state: AsyncMock = Depends(mock_get_state),
    _mls: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    _meh: AsyncMock = Depends(mock_energy_history),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Tests that the coordinator handles auth errors."""
    mock_get_state.side_effect = ERROR_AUTH
    _load_translations(hass)

    await setup_platform(hass, [Platform.BINARY_SENSOR])

    freezer.tick(WAIT)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_get_state.assert_called_once()


@test
async def coordinator_connection(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_get_state: AsyncMock = Depends(mock_get_state),
    _mls: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    _meh: AsyncMock = Depends(mock_energy_history),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Tests that the coordinator handles connection errors."""
    mock_get_state.side_effect = ERROR_CONNECTION
    _load_translations(hass)

    entry = await setup_platform(hass, [Platform.BINARY_SENSOR])
    coordinator = entry.runtime_data.vehicles[0].data_coordinator
    freezer.tick(WAIT)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_get_state.assert_called_once()
    expect(hass.states.get("binary_sensor.test_status").state).to_equal(
        STATE_UNAVAILABLE
    )
    expect(isinstance(coordinator.last_exception, UpdateFailed)).to_be(True)
    expect(coordinator.last_exception.translation_domain).to_equal(DOMAIN)
    expect(coordinator.last_exception.translation_key).to_equal("cannot_connect")


@test
async def coordinator_live_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _mgs: AsyncMock = Depends(mock_get_state),
    mock_live_status: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    _meh: AsyncMock = Depends(mock_energy_history),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Tests that the energy live coordinator handles fleet errors."""
    _load_translations(hass)

    entry = await setup_platform(hass, [Platform.SENSOR])
    coordinator = entry.runtime_data.energysites[0].live_coordinator
    expect(coordinator is not None).to_be(True)

    mock_live_status.reset_mock()
    mock_live_status.side_effect = Forbidden
    freezer.tick(TESSIE_FLEET_API_SYNC_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_live_status.assert_called_once()
    expect(hass.states.get("sensor.energy_site_solar_power").state).to_equal(
        STATE_UNAVAILABLE
    )
    expect(isinstance(coordinator.last_exception, UpdateFailed)).to_be(True)
    expect(coordinator.last_exception.translation_domain).to_equal(DOMAIN)
    expect(coordinator.last_exception.translation_key).to_equal("cannot_connect")


@test
async def coordinator_info_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _mgs: AsyncMock = Depends(mock_get_state),
    _mls: AsyncMock = Depends(mock_live_status),
    mock_site_info: AsyncMock = Depends(mock_site_info),
    _meh: AsyncMock = Depends(mock_energy_history),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Tests that the energy info coordinator handles fleet errors."""
    _load_translations(hass)

    entry = await setup_platform(hass, [Platform.SENSOR])
    coordinator = entry.runtime_data.energysites[0].info_coordinator

    mock_site_info.reset_mock()
    mock_site_info.side_effect = Forbidden
    freezer.tick(TESSIE_FLEET_API_SYNC_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_site_info.assert_called_once()
    expect(
        hass.states.get("sensor.energy_site_vpp_backup_reserve").state
    ).to_equal(STATE_UNAVAILABLE)
    expect(isinstance(coordinator.last_exception, UpdateFailed)).to_be(True)
    expect(coordinator.last_exception.translation_domain).to_equal(DOMAIN)
    expect(coordinator.last_exception.translation_key).to_equal("cannot_connect")


@test.cases(
    test.case("live_invalid", mock_fixture="mock_live_status", side_effect=InvalidToken),
    test.case("info_invalid", mock_fixture="mock_site_info", side_effect=InvalidToken),
    test.case("info_missing", mock_fixture="mock_site_info", side_effect=MissingToken),
    test.case(
        "history_invalid",
        mock_fixture="mock_energy_history",
        side_effect=InvalidToken,
    ),
    test.case(
        "history_missing",
        mock_fixture="mock_energy_history",
        side_effect=MissingToken,
    ),
)
async def coordinator_reauth(
    mock_fixture: str,
    side_effect: type[Exception],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _mgs: AsyncMock = Depends(mock_get_state),
    mls: AsyncMock = Depends(mock_live_status),
    msi: AsyncMock = Depends(mock_site_info),
    meh: AsyncMock = Depends(mock_energy_history),
) -> None:
    """Tests that energy coordinators handle auth errors."""
    fixtures = {
        "mock_live_status": mls,
        "mock_site_info": msi,
        "mock_energy_history": meh,
    }
    mock = fixtures[mock_fixture]
    mock.side_effect = side_effect
    _load_translations(hass)

    entry = await setup_platform(hass, [Platform.SENSOR])
    expect(entry.state is ConfigEntryState.SETUP_ERROR).to_be(True)


@test
async def coordinator_energy_history_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _mgs: AsyncMock = Depends(mock_get_state),
    _mls: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    mock_energy_history: AsyncMock = Depends(mock_energy_history),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Tests that the energy history coordinator handles fleet errors."""
    _load_translations(hass)

    entry = await setup_platform(hass, [Platform.SENSOR])
    coordinator = entry.runtime_data.energysites[0].history_coordinator
    expect(coordinator is not None).to_be(True)

    mock_energy_history.reset_mock()
    mock_energy_history.side_effect = Forbidden
    freezer.tick(TESSIE_ENERGY_HISTORY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_energy_history.assert_called_once()
    expect(hass.states.get("sensor.energy_site_grid_imported").state).to_equal(
        STATE_UNAVAILABLE
    )
    expect(isinstance(coordinator.last_exception, UpdateFailed)).to_be(True)
    expect(coordinator.last_exception.translation_domain).to_equal(DOMAIN)
    expect(coordinator.last_exception.translation_key).to_equal("cannot_connect")


@test
async def coordinator_energy_history_invalid_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _mgs: AsyncMock = Depends(mock_get_state),
    _mls: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    mock_energy_history: AsyncMock = Depends(mock_energy_history),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Tests that the energy history coordinator handles invalid data gracefully."""
    _load_translations(hass)

    entry = await setup_platform(hass, [Platform.SENSOR])
    coordinator = entry.runtime_data.energysites[0].history_coordinator
    expect(coordinator is not None).to_be(True)

    state_before = hass.states.get("sensor.energy_site_grid_imported").state

    mock_energy_history.reset_mock()
    mock_energy_history.side_effect = lambda *a, **kw: {"response": {}}
    freezer.tick(TESSIE_ENERGY_HISTORY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_energy_history.assert_called_once()

    expect(hass.states.get("sensor.energy_site_grid_imported").state).to_equal(
        state_before
    )
    expect(coordinator.last_exception is None).to_be(True)


@test
async def coordinator_energy_history_cold_start_invalid_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _mgs: AsyncMock = Depends(mock_get_state),
    _mls: AsyncMock = Depends(mock_live_status),
    _msi: AsyncMock = Depends(mock_site_info),
    mock_energy_history: AsyncMock = Depends(mock_energy_history),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Tests cold-start fallback when the very first energy history fetch has invalid data."""
    mock_energy_history.side_effect = lambda *a, **kw: {"response": {}}
    _load_translations(hass)

    entry = await setup_platform(hass, [Platform.SENSOR])
    coordinator = entry.runtime_data.energysites[0].history_coordinator
    expect(coordinator is not None).to_be(True)

    expect(coordinator.last_exception is None).to_be(True)
    expect(coordinator.data).to_equal({})

    expect(hass.states.get("sensor.energy_site_grid_imported").state).to_equal(
        STATE_UNKNOWN
    )

    mock_energy_history.side_effect = lambda *a, **kw: deepcopy(ENERGY_HISTORY)
    mock_energy_history.reset_mock()
    freezer.tick(TESSIE_ENERGY_HISTORY_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    mock_energy_history.assert_called_once()

    expect(coordinator.last_exception is None).to_be(True)
    expect(coordinator.data["solar_energy_exported"]).to_equal(724)
