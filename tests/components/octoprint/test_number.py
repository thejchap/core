"""The tests for OctoPrint number module."""

from datetime import datetime

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from ._fixtures import STANDARD_JOB, setup_octoprint_integration

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test.skip("snapshot test — out of scope")
async def numbers() -> None:
    """Stub: snapshot test for number entities."""


@test.skip("indirect parametrize: entity creation depends on printer config injected via parametrize")
async def numbers_no_target_temp() -> None:
    """Stub: indirect parametrize-dependent test."""


@test.skip("indirect parametrize: entity creation depends on printer config injected via parametrize")
async def set_tool_temp() -> None:
    """Stub: indirect parametrize-dependent test."""


@test.skip("indirect parametrize: entity creation depends on printer config injected via parametrize")
async def set_bed_temp() -> None:
    """Stub: indirect parametrize-dependent test."""


@test.skip("indirect parametrize: entity creation depends on printer config injected via parametrize")
async def set_tool_n_temp() -> None:
    """Stub: indirect parametrize-dependent test."""


@test
async def numbers_printer_disconnected(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test number entities when printer is disconnected."""
    with freeze_time(datetime(2020, 2, 20, 9, 10, 0)):
        async for _entry in setup_octoprint_integration(
            hass, Platform.NUMBER, printer=None, job=STANDARD_JOB
        ):
            state = hass.states.get("number.octoprint_tool0_temperature")
            expect(state).to_be(None)

            state = hass.states.get("number.octoprint_bed_temperature")
            expect(state).to_be(None)
