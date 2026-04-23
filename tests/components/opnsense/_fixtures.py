"""Tryke fixtures for the opnsense integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

from homeassistant.components.device_tracker.legacy import Device


@fixture
def mock_device_tracker_conf() -> Generator[list[Device]]:
    """Prevent device tracker from reading/writing data."""
    devices: list[Device] = []

    async def mock_update_config(path: str, dev_id: str, entity: Device) -> None:
        devices.append(entity)

    with (
        patch(
            (
                "homeassistant.components.device_tracker.legacy"
                ".DeviceTracker.async_update_config"
            ),
            side_effect=mock_update_config,
        ),
        patch(
            "homeassistant.components.device_tracker.legacy.async_load_config",
            side_effect=lambda *args: devices,
        ),
    ):
        yield devices
