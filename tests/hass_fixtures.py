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
from typing import Any

from tryke import Depends, fixture

from homeassistant.helpers import frame, translation as translation_helper
from homeassistant.util import dt as dt_util  # noqa: F401  (side effects on import)
import homeassistant.core as ha
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util.async_ import create_eager_task

from .common import async_test_home_assistant, get_test_config_dir, mock_storage


@fixture
def hass_storage() -> Generator[dict[str, Any], None, None]:
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
    hass_storage: dict[str, Any] = Depends(hass_storage),  # noqa: ARG001
) -> AsyncGenerator[HomeAssistant, None]:
    """Create a test instance of Home Assistant.

    Minimum viable port of the legacy ``hass`` fixture: omits the
    recorder tripwire, IGNORE_UNCAUGHT_EXCEPTIONS bypass, and
    fixture_setup signal; those return when their consumers migrate.
    """
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
