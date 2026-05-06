"""Tryke fixtures for RDW integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture
from vehicle import Vehicle

from homeassistant.components.rdw.const import CONF_LICENSE_PLATE, DOMAIN

from tests.common import MockConfigEntry, load_fixture


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
