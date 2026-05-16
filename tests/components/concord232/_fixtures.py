"""Tryke fixtures for the Concord232 integration."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture

from tests.hass_fixtures import mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_concord232_client() -> Generator[MagicMock]:
    """Mock the concord232 Client for easier testing."""
    with (
        patch(
            "homeassistant.components.concord232.alarm_control_panel.concord232_client.Client",
            autospec=True,
        ) as mock_client_class,
        patch(
            "homeassistant.components.concord232.binary_sensor.concord232_client.Client",
            new=mock_client_class,
        ),
    ):
        mock_instance = mock_client_class.return_value

        # Set up default return values
        mock_instance.list_partitions.return_value = [{"arming_level": "Off"}]
        mock_instance.list_zones.return_value = [
            {"number": 1, "name": "Zone 1", "state": "Normal"},
            {"number": 2, "name": "Zone 2", "state": "Normal"},
        ]

        yield mock_instance
