"""Tests for the importlib helper."""

import time
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import importlib

from tests.common import MockModule
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def async_import_module(hass: HomeAssistant = Depends(hass)) -> None:
    """Test importing a module."""
    mock_module = MockModule()
    with patch(
        "homeassistant.helpers.importlib.importlib.import_module",
        return_value=mock_module,
    ):
        module = await importlib.async_import_module(hass, "test.module")

    expect(module is mock_module).to_be(True)


@test
async def async_import_module_on_helper(hass: HomeAssistant = Depends(hass)) -> None:
    """Test importing the importlib helper."""
    module = await importlib.async_import_module(
        hass, "homeassistant.helpers.importlib"
    )
    expect(module is importlib).to_be(True)
    module = await importlib.async_import_module(
        hass, "homeassistant.helpers.importlib"
    )
    expect(module is importlib).to_be(True)


@test
async def async_import_module_failures(hass: HomeAssistant = Depends(hass)) -> None:
    """Test importing a module fails."""
    caught: Exception | None = None
    with patch(
        "homeassistant.helpers.importlib.importlib.import_module",
        side_effect=ValueError,
    ):
        try:
            await importlib.async_import_module(hass, "test.module")
        except ValueError as exc:
            caught = exc
    expect(caught).not_.to_be_none()

    mock_module = MockModule()
    # The failure should be not be cached
    with patch(
        "homeassistant.helpers.importlib.importlib.import_module",
        return_value=mock_module,
    ):
        expect(
            await importlib.async_import_module(hass, "test.module") is mock_module
        ).to_be(True)


@test
async def async_import_module_failure_caches_module_not_found(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test importing a module caches ModuleNotFound."""
    caught: Exception | None = None
    with patch(
        "homeassistant.helpers.importlib.importlib.import_module",
        side_effect=ModuleNotFoundError,
    ):
        try:
            await importlib.async_import_module(hass, "test.module")
        except ModuleNotFoundError as exc:
            caught = exc
    expect(caught).not_.to_be_none()

    mock_module = MockModule()
    # The failure should be cached
    caught = None
    with patch(
        "homeassistant.helpers.importlib.importlib.import_module",
        return_value=mock_module,
    ):
        try:
            await importlib.async_import_module(hass, "test.module")
        except ModuleNotFoundError as exc:
            caught = exc
    expect(caught).not_.to_be_none()


@test.cases(
    test.case("eager_start_true", eager_start=True),
    test.case("eager_start_false", eager_start=False),
)
async def async_import_module_concurrency(
    eager_start: bool, hass: HomeAssistant = Depends(hass)
) -> None:
    """Test importing a module with concurrency."""
    mock_module = MockModule()

    def _mock_import(name: str, *args: Any) -> MockModule:
        time.sleep(0.1)
        return mock_module

    with patch(
        "homeassistant.helpers.importlib.importlib.import_module",
        _mock_import,
    ):
        task1 = hass.async_create_task(
            importlib.async_import_module(hass, "test.module"), eager_start=eager_start
        )
        task2 = hass.async_create_task(
            importlib.async_import_module(hass, "test.module"), eager_start=eager_start
        )
        module1 = await task1
        module2 = await task2

    expect(module1 is mock_module).to_be(True)
    expect(module2 is mock_module).to_be(True)
