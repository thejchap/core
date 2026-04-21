"""Shared Tryke fixtures for Home Assistant tests.

This module is the lexical-fixture equivalent of the legacy pytest
``conftest.py`` hass-fixture tree. Under Tryke, fixtures are not
inherited via conftest; consumer tests must import the fixtures they
need and wire them explicitly with ``Depends()`` in the test signature.

Minimum viable port — the first pilot slice only touches ``hass``.
Dependencies that are only meaningful in recorder / integration tests
(``mock_recorder_before_hass``, ``hass_fixture_setup`` used as a
recorder-before-hass tripwire, ``request``-driven
``IGNORE_UNCAUGHT_EXCEPTIONS`` bypass) are intentionally omitted here
and will be added back when subsequent slices need them.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator
import logging
from pathlib import Path
import tempfile
from typing import Any

from tryke import Depends, fixture

from homeassistant.config_entries import ConfigEntryState
import homeassistant.core as ha
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    category_registry as cr,
    device_registry as dr,
    entity_registry as er,
    floor_registry as fr,
    frame,
    issue_registry as ir,
    label_registry as lr,
    translation as translation_helper,
)
from homeassistant.util import dt as dt_util  # noqa: F401  (side effects on import)
from homeassistant.util.async_ import create_eager_task

from .common import async_test_home_assistant, get_test_config_dir, mock_storage
from .test_util.aiohttp import AiohttpClientMocker, mock_aiohttp_client


@fixture
def hass_storage() -> Generator[dict[str, Any]]:
    """Mock the Home Assistant storage layer for the duration of a test."""
    with mock_storage() as stored_data:
        yield stored_data


@fixture
def load_registries() -> bool:
    """Control whether registries are loaded during hass setup.

    Tests that need to suppress registry loading should define their
    own @fixture named ``load_registries`` that returns False and wire
    it via Depends in the hass consumer instead of this one.
    """
    return True


@fixture
def hass_config_dir() -> str:
    """Provide a test config directory."""
    return get_test_config_dir()


@fixture
async def hass(
    load_registries: bool = Depends(load_registries),
    hass_config_dir: str = Depends(hass_config_dir),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> AsyncGenerator[HomeAssistant]:
    """Create a test instance of Home Assistant.

    Minimum viable port of the legacy ``hass`` fixture: omits the
    recorder tripwire, IGNORE_UNCAUGHT_EXCEPTIONS bypass, and
    fixture_setup signal; those return when their consumers migrate.
    """
    del hass_storage  # side-effect fixture; storage patch already active
    loop = asyncio.get_running_loop()

    exceptions: list[BaseException] = []

    def exc_handle(loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
        if "exception" in context:
            exceptions.append(context["exception"])
        else:
            exceptions.append(
                Exception(
                    "Received exception handler without exception, "
                    f"but with message: {context['message']}"
                )
            )
        orig_exception_handler(loop, context)

    async with async_test_home_assistant(
        loop, load_registries, config_dir=hass_config_dir
    ) as hass_inst:
        orig_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(exc_handle)
        frame.async_setup(hass_inst)

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
                        hass_inst.config_entries.async_unload(config_entry.entry_id),
                        loop=hass_inst.loop,
                    )
                    for config_entry in loaded_entries
                )
            )

        await hass_inst.async_stop(force=True)

    for ex in exceptions:
        raise ex


@fixture
async def hass_unloaded(
    hass_config_dir: str = Depends(hass_config_dir),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> AsyncGenerator[HomeAssistant]:
    """Create a hass instance with registries NOT pre-loaded.

    Equivalent to the pytest pattern
    ``@pytest.mark.parametrize("load_registries", [False])``.
    Tests that need to populate hass_storage manually and call
    ``<registry>.async_load(hass)`` themselves should depend on this
    fixture instead of ``hass``.
    """
    del hass_storage  # side-effect fixture; storage patch already active
    loop = asyncio.get_running_loop()

    exceptions: list[BaseException] = []

    def exc_handle(loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
        if "exception" in context:
            exceptions.append(context["exception"])
        else:
            exceptions.append(
                Exception(
                    "Received exception handler without exception, "
                    f"but with message: {context['message']}"
                )
            )
        orig_exception_handler(loop, context)

    async with async_test_home_assistant(
        loop, False, config_dir=hass_config_dir
    ) as hass_inst:
        orig_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(exc_handle)
        frame.async_setup(hass_inst)

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
                        hass_inst.config_entries.async_unload(config_entry.entry_id),
                        loop=hass_inst.loop,
                    )
                    for config_entry in loaded_entries
                )
            )

        await hass_inst.async_stop(force=True)

    for ex in exceptions:
        raise ex


@fixture
def aioclient_mock() -> Generator[AiohttpClientMocker]:
    """Mock aioclient calls."""
    with mock_aiohttp_client() as mock_session:
        yield mock_session


@fixture
def area_registry(hass: HomeAssistant = Depends(hass)) -> ar.AreaRegistry:
    """Return the area registry from the current hass instance."""
    return ar.async_get(hass)


@fixture
def category_registry(hass: HomeAssistant = Depends(hass)) -> cr.CategoryRegistry:
    """Return the category registry from the current hass instance."""
    return cr.async_get(hass)


@fixture
def device_registry(hass: HomeAssistant = Depends(hass)) -> dr.DeviceRegistry:
    """Return the device registry from the current hass instance."""
    return dr.async_get(hass)


@fixture
def entity_registry(hass: HomeAssistant = Depends(hass)) -> er.EntityRegistry:
    """Return the entity registry from the current hass instance."""
    return er.async_get(hass)


@fixture
def floor_registry(hass: HomeAssistant = Depends(hass)) -> fr.FloorRegistry:
    """Return the floor registry from the current hass instance."""
    return fr.async_get(hass)


@fixture
def issue_registry(hass: HomeAssistant = Depends(hass)) -> ir.IssueRegistry:
    """Return the issue registry from the current hass instance."""
    return ir.async_get(hass)


@fixture
def label_registry(hass: HomeAssistant = Depends(hass)) -> lr.LabelRegistry:
    """Return the label registry from the current hass instance."""
    return lr.async_get(hass)


class LogCapture:
    """Minimum-viable drop-in for ``pytest.LogCaptureFixture``.

    Only the members actually used by ported HA tests are implemented:
    ``text`` for substring assertions, ``records`` for per-record
    inspection, ``set_level`` / ``at_level`` for scoped level control,
    and ``clear`` for resetting between assertions.
    """

    def __init__(self) -> None:
        """Initialize an empty capture."""
        self.records: list[logging.LogRecord] = []
        self._handler = _ListHandler(self.records)
        self._root = logging.getLogger()
        self._prev_level = self._root.level

    @property
    def text(self) -> str:
        """Formatted text of all captured records."""
        return "\n".join(self._handler.format(r) for r in self.records)

    @property
    def messages(self) -> list[str]:
        """Return list of formatted messages (no level/logger prefix)."""
        return [r.getMessage() for r in self.records]

    def set_level(self, level: int | str, logger: str | None = None) -> None:
        """Set the capture level."""
        target = logging.getLogger(logger) if logger else self._root
        target.setLevel(level)

    def at_level(self, level: int | str, logger: str | None = None) -> _AtLevel:
        """Scoped level change, restored on __exit__."""
        return _AtLevel(self, level, logger)

    def clear(self) -> None:
        """Drop all captured records."""
        self.records.clear()

    def get_records(self, when: str) -> list[logging.LogRecord]:
        """Return records for a test phase.

        Tryke does not expose a pytest-style phase model, so all records
        are returned regardless of ``when`` — this mirrors caplog's
        "call" phase which is the only one HA tests actually ask for.
        """
        return list(self.records)


class _ListHandler(logging.Handler):
    """Capture records into an externally-held list."""

    def __init__(self, sink: list[logging.LogRecord]) -> None:
        super().__init__()
        self._sink = sink
        self.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        self._sink.append(record)


class _AtLevel:
    """Context manager for LogCapture.at_level()."""

    def __init__(self, cap: LogCapture, level: int | str, logger: str | None) -> None:
        self._target = logging.getLogger(logger) if logger else logging.getLogger()
        self._level = level
        self._prev: int | None = None

    def __enter__(self) -> _AtLevel:
        self._prev = self._target.level
        self._target.setLevel(self._level)
        return self

    def __exit__(self, *exc: object) -> None:
        if self._prev is not None:
            self._target.setLevel(self._prev)


@fixture
def caplog() -> Generator[LogCapture]:
    """Capture log records for the duration of a test."""
    cap = LogCapture()
    root = logging.getLogger()
    prev_level = root.level
    root.setLevel(logging.DEBUG)
    root.addHandler(cap._handler)
    try:
        yield cap
    finally:
        root.removeHandler(cap._handler)
        root.setLevel(prev_level)


@fixture
def freezer() -> Generator[Any]:
    """Drop-in replacement for pytest-freezer's ``freezer`` fixture."""
    from freezegun import freeze_time  # noqa: PLC0415

    with freeze_time() as frozen:
        yield frozen


@fixture
def tmp_path() -> Generator[Path]:
    """Drop-in replacement for pytest's ``tmp_path`` fixture."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)
