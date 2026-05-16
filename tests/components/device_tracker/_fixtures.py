"""Tryke fixtures for device_tracker tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

import homeassistant.core as ha
from homeassistant.components.device_tracker import legacy
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame, translation as translation_helper
from homeassistant.util.async_ import create_eager_task

from .common import MockScanner, mock_legacy_device_tracker_setup

from tests.common import async_test_home_assistant
from tests.hass_fixtures import (
    hass_storage as hass_storage_fx,
    load_registries as load_registries_fx,
    tmp_path as tmp_path_fx,
)


# Per-test tmp config dir matches the pytest ``hass_tmp_config_dir`` pattern
# from ``tests/components/device_tracker/conftest.py`` so the legacy YAML
# writer doesn't scribble into ``testing_config``.


@fixture
def hass_config_dir(tmp_path: Path = Depends(tmp_path_fx)) -> str:
    """Override the default hass config dir with a per-test tmp dir."""
    return str(tmp_path)


@fixture
async def hass(
    load_registries: bool = Depends(load_registries_fx),
    hass_config_dir: str = Depends(hass_config_dir),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> AsyncGenerator[HomeAssistant]:
    """Provide a hass instance backed by a per-test tmp config dir."""
    del hass_storage  # side-effect fixture; storage patch already active
    loop = asyncio.get_running_loop()
    exceptions: list[BaseException] = []

    def exc_handle(
        loop: asyncio.AbstractEventLoop, context: dict[str, Any]
    ) -> None:
        if "exception" in context:
            exceptions.append(context["exception"])
        else:
            exceptions.append(
                Exception(
                    "Received exception handler without exception, "
                    f"but with message: {context['message']}"
                )
            )
        if orig_exception_handler is not None:
            orig_exception_handler(loop, context)
        else:
            loop.default_exception_handler(context)

    async with async_test_home_assistant(
        loop, load_registries, config_dir=hass_config_dir
    ) as hass_inst:
        orig_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(exc_handle)
        frame.async_setup(hass_inst)
        hass_inst._captured_loop_exceptions = exceptions  # type: ignore[attr-defined]
        await translation_helper.async_load_integrations(hass_inst, {ha.DOMAIN})

        yield hass_inst

        loaded_entries = [
            entry
            for entry in hass_inst.config_entries.async_entries()
            if entry.state is ConfigEntryState.LOADED
        ]
        if loaded_entries:
            await asyncio.gather(
                *(
                    create_eager_task(
                        hass_inst.config_entries.async_unload(entry.entry_id),
                        loop=hass_inst.loop,
                    )
                    for entry in loaded_entries
                )
            )
        await hass_inst.async_stop(force=True)

    for ex in exceptions:
        msg = str(ex)
        if isinstance(ex, RuntimeError) and (
            "Event loop is closed" in msg or "Loop is closed" in msg
        ):
            continue
        raise ex


@fixture
def mock_legacy_device_scanner() -> MockScanner:
    """Return mocked legacy device scanner entity."""
    return MockScanner()


@fixture
def mock_legacy_setup(
    hass: HomeAssistant = Depends(hass),
    mock_legacy_device_scanner: MockScanner = Depends(mock_legacy_device_scanner),
) -> None:
    """Autouse-equivalent: mock the legacy device tracker platform setup."""
    mock_legacy_device_tracker_setup(hass, mock_legacy_device_scanner)


@fixture
def yaml_devices(
    hass: HomeAssistant = Depends(hass),
    _setup: None = Depends(mock_legacy_setup),
) -> str:
    """Return path for storing yaml devices."""
    return hass.config.path(legacy.YAML_DEVICES)


@fixture
def mock_device_tracker_conf() -> Generator[list[legacy.Device]]:
    """Prevent device tracker from reading/writing data."""
    devices: list[legacy.Device] = []

    async def mock_update_config(path: str, dev_id: str, entity: legacy.Device) -> None:
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
