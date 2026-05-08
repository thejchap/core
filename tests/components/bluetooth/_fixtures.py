"""Tryke fixtures for the bluetooth integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def macos_adapter() -> Generator[None]:
    """Fixture that mocks the macos adapter (subset of pytest version)."""
    with (
        patch(
            "homeassistant.components.bluetooth.platform.system",
            return_value="Darwin",
        ),
        patch(
            "habluetooth.scanner.platform.system",
            return_value="Darwin",
        ),
        patch(
            "bluetooth_adapters.systems.platform.system",
            return_value="Darwin",
        ),
        patch("habluetooth.scanner.SYSTEM", "Darwin"),
    ):
        yield
