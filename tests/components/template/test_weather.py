"""The tests for the Template Weather platform."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components.weather import (
    ATTR_WEATHER_APPARENT_TEMPERATURE,
    ATTR_WEATHER_CLOUD_COVERAGE,
    ATTR_WEATHER_DEW_POINT,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_OZONE,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_UV_INDEX,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_GUST_SPEED,
    ATTR_WEATHER_WIND_SPEED,
    DOMAIN as WEATHER_DOMAIN,
)
from homeassistant.const import ATTR_ATTRIBUTION, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from ._fixtures import (
    ConfigurationStyle,
    TemplatePlatformSetup,
    async_trigger,
    make_test_trigger,
    setup_entity,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_STATE_ENTITY_ID = "weather.test_state"
TEST_SENSORS = (
    "sensor.apparent_temperature",
    "sensor.attribution",
    "sensor.cloud_coverage",
    "sensor.condition",
    "sensor.dew_point",
    "sensor.forecast",
    "sensor.forecast_daily",
    "sensor.forecast_hourly",
    "sensor.forecast_twice_daily",
    "sensor.humidity",
    "sensor.ozone",
    "sensor.pressure",
    "sensor.temperature",
    "sensor.uv_index",
    "sensor.visibility",
    "sensor.wind_bearing",
    "sensor.wind_gust_speed",
    "sensor.wind_speed",
)
TEST_WEATHER = TemplatePlatformSetup(
    WEATHER_DOMAIN,
    None,
    "template_weather",
    make_test_trigger(TEST_STATE_ENTITY_ID, *TEST_SENSORS),
)

TEST_LEGACY_REQUIRED = {
    "condition_template": "sunny",
    "temperature_template": "{{ 20 }}",
    "humidity_template": "{{ 25 }}",
}

TEST_MODERN_REQUIRED = {
    "condition": "sunny",
    "temperature": "{{ 20 }}",
    "humidity": "{{ 25 }}",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


@test
async def legacy_template_creates_no_entity(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test legacy YAML configuration does not create entities."""
    await setup_entity(
        hass, TEST_WEATHER, ConfigurationStyle.LEGACY, 1, TEST_LEGACY_REQUIRED
    )
    expect(len(hass.states.async_all("weather"))).to_equal(0)


@test.cases(
    test.case("modern", style=ConfigurationStyle.MODERN),
    test.case("trigger", style=ConfigurationStyle.TRIGGER),
)
async def template_state_exception(
    *,
    style: ConfigurationStyle,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test condition produces exception."""
    await setup_entity(
        hass,
        TEST_WEATHER,
        style,
        1,
        {
            "condition": "{{ x - 2 }}",
            "temperature": "{{ 20 }}",
            "humidity": "{{ 25 }}",
        },
    )
    await async_trigger(hass, "sensor.condition", "anything")
    state = hass.states.get(TEST_WEATHER.entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_be(STATE_UNAVAILABLE)


_TEMPLATE_STATE_ATTRS = (
    ("sensor.apparent_temperature", ATTR_WEATHER_APPARENT_TEMPERATURE, 25),
    ("sensor.attribution", ATTR_ATTRIBUTION, "Custom"),
    ("sensor.cloud_coverage", ATTR_WEATHER_CLOUD_COVERAGE, 75),
    ("sensor.dew_point", ATTR_WEATHER_DEW_POINT, 2.2),
    ("sensor.humidity", ATTR_WEATHER_HUMIDITY, 60),
    ("sensor.ozone", ATTR_WEATHER_OZONE, 25),
    ("sensor.pressure", ATTR_WEATHER_PRESSURE, 1000),
    ("sensor.temperature", ATTR_WEATHER_TEMPERATURE, 22.3),
    ("sensor.uv_index", ATTR_WEATHER_UV_INDEX, 3.7),
    ("sensor.visibility", ATTR_WEATHER_VISIBILITY, 4.6),
    ("sensor.wind_bearing", ATTR_WEATHER_WIND_BEARING, 180),
    ("sensor.wind_gust_speed", ATTR_WEATHER_WIND_GUST_SPEED, 30),
    ("sensor.wind_speed", ATTR_WEATHER_WIND_SPEED, 20),
)


@test.cases(
    test.case(
        "modern_legacy_keys",
        style=ConfigurationStyle.MODERN,
        config={
            "apparent_temperature_template": "{{ states('sensor.apparent_temperature') }}",
            "attribution_template": "{{ states('sensor.attribution') }}",
            "cloud_coverage_template": "{{ states('sensor.cloud_coverage') }}",
            "condition_template": "{{ states('sensor.condition') }}",
            "dew_point_template": "{{ states('sensor.dew_point') }}",
            "humidity_template": "{{ states('sensor.humidity') | int }}",
            "ozone_template": "{{ states('sensor.ozone') }}",
            "pressure_template": "{{ states('sensor.pressure') }}",
            "temperature_template": "{{ states('sensor.temperature') | float }}",
            "unique_id": "abc123",
            "uv_index_template": "{{ states('sensor.uv_index') }}",
            "visibility_template": "{{ states('sensor.visibility') }}",
            "wind_bearing_template": "{{ states('sensor.wind_bearing') }}",
            "wind_gust_speed_template": "{{ states('sensor.wind_gust_speed') }}",
            "wind_speed_template": "{{ states('sensor.wind_speed') }}",
        },
    ),
    test.case(
        "modern_modern_keys",
        style=ConfigurationStyle.MODERN,
        config={
            "apparent_temperature": "{{ states('sensor.apparent_temperature') }}",
            "attribution": "{{ states('sensor.attribution') }}",
            "cloud_coverage": "{{ states('sensor.cloud_coverage') }}",
            "condition": "{{ states('sensor.condition') }}",
            "dew_point": "{{ states('sensor.dew_point') }}",
            "humidity": "{{ states('sensor.humidity') | int }}",
            "ozone": "{{ states('sensor.ozone') }}",
            "pressure": "{{ states('sensor.pressure') }}",
            "temperature": "{{ states('sensor.temperature') | float }}",
            "unique_id": "abc123",
            "uv_index": "{{ states('sensor.uv_index') }}",
            "visibility": "{{ states('sensor.visibility') }}",
            "wind_bearing": "{{ states('sensor.wind_bearing') }}",
            "wind_gust_speed": "{{ states('sensor.wind_gust_speed') }}",
            "wind_speed": "{{ states('sensor.wind_speed') }}",
        },
    ),
    test.case(
        "trigger_modern_keys",
        style=ConfigurationStyle.TRIGGER,
        config={
            "apparent_temperature": "{{ states('sensor.apparent_temperature') }}",
            "attribution": "{{ states('sensor.attribution') }}",
            "cloud_coverage": "{{ states('sensor.cloud_coverage') }}",
            "condition": "{{ states('sensor.condition') }}",
            "dew_point": "{{ states('sensor.dew_point') }}",
            "humidity": "{{ states('sensor.humidity') }}",
            "ozone": "{{ states('sensor.ozone') }}",
            "pressure": "{{ states('sensor.pressure') }}",
            "temperature": "{{ states('sensor.temperature') }}",
            "unique_id": "abc123",
            "uv_index": "{{ states('sensor.uv_index') }}",
            "visibility": "{{ states('sensor.visibility') }}",
            "wind_bearing": "{{ states('sensor.wind_bearing') }}",
            "wind_gust_speed": "{{ states('sensor.wind_gust_speed') }}",
            "wind_speed": "{{ states('sensor.wind_speed') }}",
        },
    ),
)
async def template_state_text(
    *,
    style: ConfigurationStyle,
    config: dict,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the state text of a template."""
    await setup_entity(hass, TEST_WEATHER, style, 1, config)
    await async_trigger(hass, "sensor.condition", "sunny")
    for entity_id, v_attr, value in _TEMPLATE_STATE_ATTRS:
        await async_trigger(hass, entity_id, str(value))
        state = hass.states.get(TEST_WEATHER.entity_id)
        expect(state).not_.to_be(None)
        expect(state.state).to_equal("sunny")
        expect(state.attributes.get(v_attr)).to_equal(value)

    await async_trigger(hass, "sensor.condition", "None")
    state = hass.states.get(TEST_WEATHER.entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_be(STATE_UNKNOWN)


@test.skip("requires snapshot fixture (syrupy) — port deferred")
async def setup_config_entry() -> None:
    """Stub: requires syrupy snapshot."""


@test.skip("requires hass_ws_client (websocket flow preview) — port deferred")
async def flow_preview() -> None:
    """Stub: requires WebSocketGenerator flow preview."""


@test.skip("forecasts requires syrupy snapshot — port deferred")
async def forecasts() -> None:
    """Stub: snapshot-based forecast assertions."""


@test.skip("forecasts_invalid requires caplog inspection — port deferred")
async def forecasts_invalid() -> None:
    """Stub."""


@test.skip("forecast_format_error requires caplog inspection — port deferred")
async def forecast_format_error() -> None:
    """Stub."""


@test.skip("trigger_entity_restore_state needs restore-cache scaffolding")
async def trigger_entity_restore_state() -> None:
    """Stub."""


@test.skip("trigger_action requires async_mock_restore_state_shutdown_restart")
async def trigger_action() -> None:
    """Stub."""


@test.skip("restore_weather_save_state requires restore-cache scaffolding")
async def restore_weather_save_state() -> None:
    """Stub."""


@test.skip("trigger_entity_restore_state_fail requires restore-cache scaffolding")
async def trigger_entity_restore_state_fail() -> None:
    """Stub."""


@test.skip("templated_optional_config — port deferred")
async def templated_optional_config() -> None:
    """Stub."""
