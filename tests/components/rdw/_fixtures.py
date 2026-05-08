"""Tryke fixtures for RDW integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture
from vehicle import Vehicle

from homeassistant.components.rdw.const import CONF_LICENSE_PLATE, DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="My Car",
        domain=DOMAIN,
        data={CONF_LICENSE_PLATE: "11ZKZ3"},
        unique_id="11ZKZ3",
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.rdw.async_setup_entry", return_value=True):
        yield


@fixture
def mock_rdw_config_flow() -> Generator[MagicMock]:
    """Return a mocked RDW client."""
    with patch(
        "homeassistant.components.rdw.config_flow.RDW", autospec=True
    ) as rdw_mock:
        rdw = rdw_mock.return_value
        rdw.vehicle.return_value = Vehicle.from_json(load_fixture("rdw/11ZKZ3.json"))
        yield rdw


@fixture
def mock_rdw() -> Generator[MagicMock]:
    """Return a mocked RDW client patched on coordinator + config_flow sites."""
    with (
        patch(
            "homeassistant.components.rdw.coordinator.RDW", autospec=True
        ) as rdw_mock,
        patch("homeassistant.components.rdw.config_flow.RDW", new=rdw_mock),
    ):
        rdw = rdw_mock.return_value
        rdw.vehicle.return_value = Vehicle.from_json(load_fixture("rdw/11ZKZ3.json"))
        yield rdw


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _rdw: MagicMock = Depends(mock_rdw),
) -> MockConfigEntry:
    """Set up the RDW integration for testing."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
