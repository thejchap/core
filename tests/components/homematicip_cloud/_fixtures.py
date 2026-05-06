"""Tryke fixtures for the homematicip_cloud integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

from homematicip.async_home import AsyncHome
from homematicip.base.enums import WeatherCondition, WeatherDayTime
from tryke import fixture


@fixture
def simple_mock_home() -> Generator[None]:
    """Return a simple mocked connection."""
    mock_home = AsyncMock(
        spec=AsyncHome,
        name="Demo",
        devices=[],
        groups=[],
        location=Mock(),
        weather=Mock(
            temperature=0.0,
            weatherCondition=WeatherCondition.UNKNOWN,
            weatherDayTime=WeatherDayTime.DAY,
            minTemperature=0.0,
            maxTemperature=0.0,
            humidity=0,
            windSpeed=0.0,
            windDirection=0,
            vaporAmount=0.0,
        ),
        id=42,
        dutyCycle=88,
        connected=True,
        currentAPVersion="2.0.36",
        init_async=AsyncMock(),
        get_current_state_async=AsyncMock(),
    )

    with (
        patch(
            "homeassistant.components.homematicip_cloud.hap.AsyncHome",
            autospec=True,
            return_value=mock_home,
        ),
        patch(
            "homeassistant.components.homematicip_cloud.hap.ConnectionContextBuilder.build_context_async",
        ),
    ):
        yield
