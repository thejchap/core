"""Tryke fixtures for the energy component tests."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.energy import async_get_manager
from homeassistant.components.energy.data import EnergyManager
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[object]:
    """Set up an in-memory recorder for energy tests."""
    yield await setup_recorder_mock(hass)


@fixture
def mock_is_entity_recorded() -> Generator[dict[str, bool]]:
    """Mock recorder.is_entity_recorded."""
    mocks: dict[str, bool] = {}

    with patch(
        "homeassistant.components.recorder.is_entity_recorded",
        side_effect=lambda hass, entity_id: mocks.get(entity_id, True),
    ):
        yield mocks


@fixture
def mock_get_metadata() -> Generator[dict[str, object]]:
    """Mock recorder.statistics.get_metadata."""
    mocks: dict[str, object] = {}

    def _get_metadata(_hass, *, statistic_ids):
        result = {}
        for statistic_id in statistic_ids:
            if statistic_id in mocks:
                if mocks[statistic_id] is not None:
                    result[statistic_id] = mocks[statistic_id]
            else:
                result[statistic_id] = (1, {})
        return result

    with patch(
        "homeassistant.components.recorder.statistics.get_metadata",
        wraps=_get_metadata,
    ):
        yield mocks


@fixture
async def mock_energy_manager(
    _recorder: object = Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
) -> EnergyManager:
    """Set up energy."""
    assert await async_setup_component(hass, "energy", {"energy": {}})
    manager = await async_get_manager(hass)
    manager.data = manager.default_preferences()
    return manager
