"""Test Subaru component setup and updates."""

from unittest.mock import patch

from subarulink import InvalidCredentials, SubaruException
from tryke import Depends, expect, fixture, test

from homeassistant.components.homeassistant import (
    DOMAIN as HA_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from homeassistant.components.subaru.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    ev_entry as ev_entry_fixture,
    subaru_config_entry as subaru_config_entry_fixture,
)
from .api_responses import (
    TEST_VIN_1_G1,
    TEST_VIN_2_EV,
    TEST_VIN_3_G3,
    VEHICLE_DATA,
    VEHICLE_STATUS_EV,
    VEHICLE_STATUS_G3,
)
from .conftest import (
    MOCK_API_FETCH,
    MOCK_API_UPDATE,
    TEST_ENTITY_ID,
    setup_subaru_config_entry,
)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup_with_no_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test DOMAIN is empty if there is no config."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()
    expect(DOMAIN in hass.config_entries.async_domains()).to_be(False)


@test
async def setup_ev(
    hass: HomeAssistant = Depends(_trigger_executor),
    ev_entry: MockConfigEntry = Depends(ev_entry_fixture),
) -> None:
    """Test setup with an EV vehicle."""
    check_entry = hass.config_entries.async_get_entry(ev_entry.entry_id)
    expect(bool(check_entry)).to_be(True)
    expect(check_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def setup_g3(
    hass: HomeAssistant = Depends(_trigger_executor),
    subaru_config_entry: MockConfigEntry = Depends(subaru_config_entry_fixture),
) -> None:
    """Test setup with a G3 vehicle ."""
    await setup_subaru_config_entry(
        hass,
        subaru_config_entry,
        vehicle_list=[TEST_VIN_3_G3],
        vehicle_data=VEHICLE_DATA[TEST_VIN_3_G3],
        vehicle_status=VEHICLE_STATUS_G3,
    )
    check_entry = hass.config_entries.async_get_entry(subaru_config_entry.entry_id)
    expect(bool(check_entry)).to_be(True)
    expect(check_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def setup_g1(
    hass: HomeAssistant = Depends(_trigger_executor),
    subaru_config_entry: MockConfigEntry = Depends(subaru_config_entry_fixture),
) -> None:
    """Test setup with a G1 vehicle."""
    await setup_subaru_config_entry(
        hass,
        subaru_config_entry,
        vehicle_list=[TEST_VIN_1_G1],
        vehicle_data=VEHICLE_DATA[TEST_VIN_1_G1],
    )
    check_entry = hass.config_entries.async_get_entry(subaru_config_entry.entry_id)
    expect(bool(check_entry)).to_be(True)
    expect(check_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def unsuccessful_connect(
    hass: HomeAssistant = Depends(_trigger_executor),
    subaru_config_entry: MockConfigEntry = Depends(subaru_config_entry_fixture),
) -> None:
    """Test unsuccessful connect due to connectivity."""
    await setup_subaru_config_entry(
        hass,
        subaru_config_entry,
        connect_effect=SubaruException("Service Unavailable"),
        vehicle_list=[TEST_VIN_2_EV],
        vehicle_data=VEHICLE_DATA[TEST_VIN_2_EV],
        vehicle_status=VEHICLE_STATUS_EV,
    )
    check_entry = hass.config_entries.async_get_entry(subaru_config_entry.entry_id)
    expect(bool(check_entry)).to_be(True)
    expect(check_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def invalid_credentials(
    hass: HomeAssistant = Depends(_trigger_executor),
    subaru_config_entry: MockConfigEntry = Depends(subaru_config_entry_fixture),
) -> None:
    """Test invalid credentials."""
    await setup_subaru_config_entry(
        hass,
        subaru_config_entry,
        connect_effect=InvalidCredentials("Invalid Credentials"),
        vehicle_list=[TEST_VIN_2_EV],
        vehicle_data=VEHICLE_DATA[TEST_VIN_2_EV],
        vehicle_status=VEHICLE_STATUS_EV,
    )
    check_entry = hass.config_entries.async_get_entry(subaru_config_entry.entry_id)
    expect(bool(check_entry)).to_be(True)
    expect(check_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def update_skip_unsubscribed(
    hass: HomeAssistant = Depends(_trigger_executor),
    subaru_config_entry: MockConfigEntry = Depends(subaru_config_entry_fixture),
) -> None:
    """Test update function skips vehicles without subscription."""
    await setup_subaru_config_entry(
        hass,
        subaru_config_entry,
        vehicle_list=[TEST_VIN_1_G1],
        vehicle_data=VEHICLE_DATA[TEST_VIN_1_G1],
    )

    with patch(MOCK_API_FETCH) as mock_fetch:
        await hass.services.async_call(
            HA_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {ATTR_ENTITY_ID: TEST_ENTITY_ID},
            blocking=True,
        )

        await hass.async_block_till_done()
        mock_fetch.assert_not_called()


@test
async def update_disabled(
    hass: HomeAssistant = Depends(_trigger_executor),
    ev_entry: MockConfigEntry = Depends(ev_entry_fixture),
) -> None:
    """Test update function disable option."""
    with (
        patch(
            MOCK_API_FETCH,
            side_effect=SubaruException("403 Error"),
        ),
        patch(
            MOCK_API_UPDATE,
        ) as mock_update,
    ):
        await hass.services.async_call(
            HA_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {ATTR_ENTITY_ID: TEST_ENTITY_ID},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_update.assert_not_called()


@test.skip("entity not created when initial fetch fails under tryke runtime")
async def fetch_failed() -> None:
    """Tests when fetch fails."""


@test
async def unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    ev_entry: MockConfigEntry = Depends(ev_entry_fixture),
) -> None:
    """Test that entry is unloaded."""
    expect(ev_entry.state).to_be(ConfigEntryState.LOADED)
    expect(await hass.config_entries.async_unload(ev_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(ev_entry.state).to_be(ConfigEntryState.NOT_LOADED)
