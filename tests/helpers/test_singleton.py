"""Test singleton helper."""

from typing import Any
from unittest.mock import Mock

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import singleton as _singleton


@fixture
def mock_hass() -> Mock:
    """Mock hass fixture."""
    return Mock(data={})


@test.cases(
    test.case("object", result=object()),
    test.case("dict", result={}),
    test.case("list", result=[]),
)
async def singleton_async(result: Any, mock_hass: Mock = Depends(mock_hass)) -> None:
    """Test singleton with async function."""

    @_singleton.singleton("test_key")
    async def something(hass: HomeAssistant) -> Any:
        return result

    result1 = await something(mock_hass)
    result2 = await something(mock_hass)
    expect(result1 is result).to_be(True)
    expect(result1 is result2).to_be(True)
    expect("test_key" in mock_hass.data).to_be(True)
    expect(mock_hass.data["test_key"] is result1).to_be(True)


@test.cases(
    test.case("object", result=object()),
    test.case("dict", result={}),
    test.case("list", result=[]),
)
def singleton(result: Any, mock_hass: Mock = Depends(mock_hass)) -> None:
    """Test singleton with function."""

    @_singleton.singleton("test_key")
    def something(hass: HomeAssistant) -> Any:
        return result

    result1 = something(mock_hass)
    result2 = something(mock_hass)
    expect(result1 is result).to_be(True)
    expect(result1 is result2).to_be(True)
    expect("test_key" in mock_hass.data).to_be(True)
    expect(mock_hass.data["test_key"] is result1).to_be(True)
