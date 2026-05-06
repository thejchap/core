"""Tryke fixtures for the Switcher integration tests."""

from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import fixture


def _make_bridge_patch(devices: list | None = None):
    """Create the SwitcherBridge mock patch context."""
    return _bridge_context(devices or [])


@contextmanager
def _bridge_context(devices: list) -> Generator[MagicMock]:
    with (
        patch(
            "homeassistant.components.switcher_kis.SwitcherBridge", autospec=True
        ) as bridge_mock,
        patch(
            "homeassistant.components.switcher_kis.utils.SwitcherBridge",
            new=bridge_mock,
        ),
    ):
        bridge = bridge_mock.return_value
        bridge.devices = devices

        async def start():
            bridge.is_running = True
            for device in bridge.devices:
                bridge_mock.call_args[0][0](device)

        def mock_callbacks(devices_to_emit):
            for device in devices_to_emit:
                bridge_mock.call_args[0][0](device)

        async def stop():
            bridge.is_running = False

        bridge.start = AsyncMock(side_effect=start)
        bridge.mock_callbacks = Mock(side_effect=mock_callbacks)
        bridge.stop = AsyncMock(side_effect=stop)
        yield bridge


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.switcher_kis.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_bridge_empty() -> Generator[MagicMock]:
    """Mock a SwitcherBridge with no devices."""
    with _bridge_context([]) as bridge:
        yield bridge
