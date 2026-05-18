"""Tests for Vallox fan platform."""

from typing import Any
from unittest.mock import call, patch

from tryke import Depends, expect, fixture, test
from vallox_websocket_api import MetricData, Profile, ValloxApiException

from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE,
    SERVICE_SET_PRESET_MODE,
    NotValidPresetModeError,
)
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ._fixtures import default_metrics, fetch_metric_data_mock, mock_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Present so tryke builds a fixture executor for this module."""
    return 0


def patch_set_profile():
    """Patch the Vallox set_profile method."""
    return patch("homeassistant.components.vallox.Vallox.set_profile")


def patch_set_fan_speed():
    """Patch the Vallox set_fan_speed method."""
    return patch("homeassistant.components.vallox.Vallox.set_fan_speed")


def patch_set_values():
    """Patch the Vallox set_values method."""
    return patch("homeassistant.components.vallox.Vallox.set_values")


def _apply_metrics(
    fetch_mock: Any,
    base_metrics: dict[str, int],
    metrics: dict[str, int] | None = None,
    metric_data_class: type[MetricData] = MetricData,
) -> Any:
    """Reconfigure the fetch_metric_data mock with merged metrics."""
    merged = {**base_metrics, **(metrics or {})}
    fetch_mock.return_value = metric_data_class(merged)
    return fetch_mock


@test.cases(
    test.case("on", metrics={"A_CYC_MODE": 0}, expected_state="on"),
    test.case("off", metrics={"A_CYC_MODE": 5}, expected_state="off"),
)
async def fan_state(
    metrics: dict[str, int],
    expected_state: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    fetch_mock: Any = Depends(fetch_metric_data_mock),
    base_metrics: dict[str, int] = Depends(default_metrics),
) -> None:
    """Test fan on/off state."""
    _apply_metrics(fetch_mock, base_metrics, metrics=metrics)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    fetch_mock.assert_called_once()
    sensor = hass.states.get("fan.vallox")
    expect(sensor).not_.to_be_none()
    expect(sensor.state).to_equal(expected_state)


@test.cases(
    test.case("home", vallox_profile=Profile.HOME, expected_preset="Home"),
    test.case("away", vallox_profile=Profile.AWAY, expected_preset="Away"),
    test.case("boost", vallox_profile=Profile.BOOST, expected_preset="Boost"),
    test.case(
        "fireplace", vallox_profile=Profile.FIREPLACE, expected_preset="Fireplace"
    ),
)
async def fan_profile(
    vallox_profile: Profile,
    expected_preset: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    fetch_mock: Any = Depends(fetch_metric_data_mock),
    base_metrics: dict[str, int] = Depends(default_metrics),
) -> None:
    """Test fan profile."""

    class MockMetricData(MetricData):
        @property
        def profile(self):
            return vallox_profile

    _apply_metrics(fetch_mock, base_metrics, metric_data_class=MockMetricData)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    sensor = hass.states.get("fan.vallox")
    expect(sensor).not_.to_be_none()
    expect(sensor.attributes["preset_mode"]).to_equal(expected_preset)


@test.cases(
    test.case(
        "turn_on",
        service=SERVICE_TURN_ON,
        initial_metrics={"A_CYC_MODE": 5},
        expected_called_with={"A_CYC_MODE": 0},
    ),
    test.case(
        "turn_off",
        service=SERVICE_TURN_OFF,
        initial_metrics={"A_CYC_MODE": 0},
        expected_called_with={"A_CYC_MODE": 5},
    ),
)
async def turn_on_off(
    service: str,
    initial_metrics: dict[str, int],
    expected_called_with: dict[str, int],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    fetch_mock: Any = Depends(fetch_metric_data_mock),
    base_metrics: dict[str, int] = Depends(default_metrics),
) -> None:
    """Test turn on/off."""
    _apply_metrics(fetch_mock, base_metrics, metrics=initial_metrics)

    with patch_set_values() as set_values:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        await hass.services.async_call(
            FAN_DOMAIN,
            service,
            service_data={ATTR_ENTITY_ID: "fan.vallox"},
            blocking=True,
        )
        set_values.assert_called_once_with(expected_called_with)


@test.cases(
    test.case(
        "from_off",
        initial_metrics={"A_CYC_MODE": 5},
        expected_calls=[
            call({"A_CYC_MODE": 0}),
            call({"A_CYC_AWAY_SPEED_SETTING": 15}),
        ],
    ),
    test.case(
        "from_on",
        initial_metrics={"A_CYC_MODE": 0},
        expected_calls=[
            call({"A_CYC_AWAY_SPEED_SETTING": 15}),
        ],
    ),
)
async def turn_on_with_parameters(
    initial_metrics: dict[str, int],
    expected_calls: list[Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    fetch_mock: Any = Depends(fetch_metric_data_mock),
    base_metrics: dict[str, int] = Depends(default_metrics),
) -> None:
    """Test turn on with parameters."""
    _apply_metrics(fetch_mock, base_metrics, metrics=initial_metrics)

    with patch_set_values() as set_values, patch_set_profile() as set_profile:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_TURN_ON,
            service_data={
                ATTR_ENTITY_ID: "fan.vallox",
                ATTR_PERCENTAGE: "15",
                ATTR_PRESET_MODE: "Away",
            },
            blocking=True,
        )
        set_profile.assert_called_once_with(Profile.AWAY)
        expect(set_values.call_args_list).to_equal(expected_calls)


@test.cases(
    test.case(
        "home_from_away",
        preset="Home",
        initial_profile=Profile.AWAY,
        expected_calls=[call(Profile.HOME)],
    ),
    test.case(
        "away_from_home",
        preset="Away",
        initial_profile=Profile.HOME,
        expected_calls=[call(Profile.AWAY)],
    ),
    test.case(
        "boost_from_home",
        preset="Boost",
        initial_profile=Profile.HOME,
        expected_calls=[call(Profile.BOOST)],
    ),
    test.case(
        "fireplace_from_home",
        preset="Fireplace",
        initial_profile=Profile.HOME,
        expected_calls=[call(Profile.FIREPLACE)],
    ),
    test.case(
        "no_change",
        preset="Home",
        initial_profile=Profile.HOME,
        expected_calls=[],
    ),
)
async def set_preset_mode(
    preset: str,
    initial_profile: Profile,
    expected_calls: list[Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    fetch_mock: Any = Depends(fetch_metric_data_mock),
    base_metrics: dict[str, int] = Depends(default_metrics),
) -> None:
    """Test set preset mode."""

    class MockMetricData(MetricData):
        @property
        def profile(self):
            return initial_profile

    _apply_metrics(fetch_mock, base_metrics, metric_data_class=MockMetricData)

    with patch_set_profile() as set_profile:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            service_data={ATTR_ENTITY_ID: "fan.vallox", ATTR_PRESET_MODE: preset},
            blocking=True,
        )
        expect(set_profile.call_args_list).to_equal(expected_calls)


@test
async def set_invalid_preset_mode(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    _fetch_mock: Any = Depends(fetch_metric_data_mock),
) -> None:
    """Test set invalid preset mode."""
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    raised: NotValidPresetModeError | None = None
    try:
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            service_data={
                ATTR_ENTITY_ID: "fan.vallox",
                ATTR_PRESET_MODE: "Invalid",
            },
            blocking=True,
        )
    except NotValidPresetModeError as exc:
        raised = exc
    expect(raised).not_.to_be_none()
    expect(raised.translation_key).to_equal("not_valid_preset_mode")


@test
async def set_preset_mode_exception(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    _fetch_mock: Any = Depends(fetch_metric_data_mock),
) -> None:
    """Test set preset mode raises HomeAssistantError on api exception."""
    with patch_set_profile() as set_profile:
        set_profile.side_effect = ValloxApiException("Fake exception")
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                FAN_DOMAIN,
                SERVICE_SET_PRESET_MODE,
                service_data={ATTR_ENTITY_ID: "fan.vallox", ATTR_PRESET_MODE: "Away"},
                blocking=True,
            )


@test.cases(
    test.case(
        "home_40",
        initial_profile=Profile.HOME,
        percentage=40,
        expected_set_fan_speed_call=[call(Profile.HOME, 40)],
        expected_set_values_call=[],
    ),
    test.case(
        "away_30",
        initial_profile=Profile.AWAY,
        percentage=30,
        expected_set_fan_speed_call=[call(Profile.AWAY, 30)],
        expected_set_values_call=[],
    ),
    test.case(
        "boost_60",
        initial_profile=Profile.BOOST,
        percentage=60,
        expected_set_fan_speed_call=[call(Profile.BOOST, 60)],
        expected_set_values_call=[],
    ),
    test.case(
        "turn_off",
        initial_profile=Profile.HOME,
        percentage=0,
        expected_set_fan_speed_call=[],
        expected_set_values_call=[call({"A_CYC_MODE": 5})],
    ),
)
async def set_fan_speed(
    initial_profile: Profile,
    percentage: int,
    expected_set_fan_speed_call: list[Any],
    expected_set_values_call: list[Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    fetch_mock: Any = Depends(fetch_metric_data_mock),
    base_metrics: dict[str, int] = Depends(default_metrics),
) -> None:
    """Test set fan speed percentage."""

    class MockMetricData(MetricData):
        @property
        def profile(self):
            return initial_profile

    _apply_metrics(
        fetch_mock,
        base_metrics,
        metrics={"A_CYC_MODE": 0},
        metric_data_class=MockMetricData,
    )

    with patch_set_fan_speed() as set_fan_speed_mock, patch_set_values() as set_values:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PERCENTAGE,
            service_data={ATTR_ENTITY_ID: "fan.vallox", ATTR_PERCENTAGE: percentage},
            blocking=True,
        )
        expect(set_fan_speed_mock.call_args_list).to_equal(expected_set_fan_speed_call)
        expect(set_values.call_args_list).to_equal(expected_set_values_call)


@test
async def set_fan_speed_exception(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    fetch_mock: Any = Depends(fetch_metric_data_mock),
    base_metrics: dict[str, int] = Depends(default_metrics),
) -> None:
    """Test set fan speed percentage exception."""
    _apply_metrics(
        fetch_mock,
        base_metrics,
        metrics={"A_CYC_MODE": 0, "A_CYC_HOME_SPEED_SETTING": 30},
    )

    with patch_set_values() as set_values:
        set_values.side_effect = ValloxApiException("Fake failure")
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                FAN_DOMAIN,
                SERVICE_SET_PERCENTAGE,
                service_data={ATTR_ENTITY_ID: "fan.vallox", ATTR_PERCENTAGE: 5},
                blocking=True,
            )
