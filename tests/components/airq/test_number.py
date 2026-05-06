"""Test the NUMBER platform from air-Q integration."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from . import setup_platform
from ._fixtures import mock_airq
from .common import TEST_BRIGHTNESS, TEST_DEVICE_INFO

from tests.hass_fixtures import hass as hass_fixture, mock_network

ENTITY_ID = f"number.{TEST_DEVICE_INFO['name']}_led_brightness"


@fixture
async def number_platform(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Configure AirQ integration and validate the setup for NUMBER platform."""
    await setup_platform(hass, Platform.NUMBER)

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert float(state.state) == TEST_BRIGHTNESS


@test.cases(
    test.case("zero", new_brightness=0),
    test.case("hundred", new_brightness=100),
    test.case("offset", new_brightness=(TEST_BRIGHTNESS + 10) % 100),
)
async def number_set_value(
    new_brightness: int,
    _setup: None = Depends(number_platform),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test that setting value works."""
    mock_airq.get_current_brightness.return_value = new_brightness

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": ENTITY_ID, "value": new_brightness},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_airq.set_current_brightness.assert_called_once_with(new_brightness)

    state = hass.states.get(ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(float(state.state)).to_equal(new_brightness)


@test.cases(
    test.case("negative", new_brightness=-1),
    test.case("over_max", new_brightness=110),
)
async def number_set_invalid_value_caught_by_hass(
    new_brightness: int,
    _setup: None = Depends(number_platform),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test that setting incorrect values errors."""
    raised: BaseException | None = None
    try:
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": ENTITY_ID, "value": new_brightness},
            blocking=True,
        )
    except BaseException as exc:  # noqa: BLE001 - test assertion
        raised = exc
    expect(raised).not_.to_be(None)
    expect(isinstance(raised, ServiceValidationError)).to_be_truthy()

    mock_airq.set_current_brightness.assert_not_called()
