"""Tests for rpi_power binary sensor."""

from datetime import timedelta
import logging
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.rpi_power import binary_sensor
from homeassistant.components.rpi_power.binary_sensor import (
    DESCRIPTION_NORMALIZED,
    DESCRIPTION_UNDER_VOLTAGE,
)
from homeassistant.components.rpi_power.const import DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)

ENTITY_ID = "binary_sensor.rpi_power_status"

MODULE = "homeassistant.components.rpi_power.binary_sensor.new_under_voltage"


async def _async_setup_component(hass: HomeAssistant, detected: bool) -> MagicMock:
    mocked_under_voltage = MagicMock()
    type(mocked_under_voltage).get = MagicMock(return_value=detected)
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    with patch(MODULE, return_value=mocked_under_voltage):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
        await hass.async_block_till_done()
    return mocked_under_voltage


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


def _record_tuples(caplog: LogCapture) -> list[tuple[str, int, str]]:
    """Mirror of pytest caplog.record_tuples."""
    return [(r.name, r.levelno, r.getMessage()) for r in caplog.records]


@test
async def new(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test new entry."""
    await _async_setup_component(hass, False)
    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(STATE_OFF)
    expect(any(x.levelno == logging.WARNING for x in caplog.records)).to_be(False)


@test
async def new_detected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test new entry with under voltage detected."""
    mocked_under_voltage = await _async_setup_component(hass, True)
    state = hass.states.get(ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_ON)
    expect(
        (
            binary_sensor.__name__,
            logging.WARNING,
            DESCRIPTION_UNDER_VOLTAGE,
        )
        in _record_tuples(caplog)
    ).to_be(True)

    type(mocked_under_voltage).get = MagicMock(return_value=False)
    future = dt_util.utcnow() + timedelta(minutes=1)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_OFF)
    expect(
        (
            binary_sensor.__name__,
            logging.DEBUG,
            DESCRIPTION_NORMALIZED,
        )
        in _record_tuples(caplog)
    ).to_be(True)
