"""Tryke fixtures for greeneye_monitor tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from .common import add_listeners

from tests.hass_fixtures import mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@fixture
def monitors() -> Generator[AsyncMock]:
    """Provide a mock greeneye.Monitors object that has listeners and can add new monitors."""
    with patch("greeneye.Monitors", autospec=True) as mock_monitors:
        mock = mock_monitors.return_value
        add_listeners(mock)
        mock.monitors = {}

        def add_monitor(monitor: MagicMock) -> None:
            """Add the given mock monitor as a monitor with the given serial number, notifying any listeners on the Monitors object."""
            serial_number = monitor.serial_number
            mock.monitors[serial_number] = monitor
            mock.notify_all_listeners(monitor)

        mock.add_monitor = add_monitor
        yield mock
