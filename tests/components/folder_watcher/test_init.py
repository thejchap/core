"""The tests for the folder_watcher component."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import folder_watcher
from homeassistant.components.folder_watcher.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def invalid_path_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    freezer=Depends(freezer_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test that an invalid path is not set up."""
    freezer.move_to("2022-04-19 10:31:02+00:00")
    path = tmp_path.as_posix()
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        title=f"Folder Watcher {path!s}",
        data={},
        options={"folder": str(path), "patterns": ["*"]},
        entry_id="1",
    )

    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(len(issue_registry.issues)).to_equal(1)


@test
async def valid_path_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test that a valid path is setup."""
    freezer.move_to("2022-04-19 10:31:02+00:00")
    path = tmp_path.as_posix()
    hass.config.allowlist_external_dirs = {path}
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        title=f"Folder Watcher {path!s}",
        data={},
        options={"folder": str(path), "patterns": ["*"]},
        entry_id="1",
    )

    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
def event() -> None:
    """Check that Home Assistant events are fired correctly on watchdog event."""

    class MockPatternMatchingEventHandler:
        """Mock base class for the pattern matcher event handler."""

        def __init__(self, patterns) -> None:
            pass

    with patch(
        "homeassistant.components.folder_watcher.PatternMatchingEventHandler",
        MockPatternMatchingEventHandler,
    ):
        hass = Mock()
        handler = folder_watcher.create_event_handler(["*"], hass, "1")
        handler.on_created(
            SimpleNamespace(
                is_directory=False, src_path="/hello/world.txt", event_type="created"
            )
        )
        expect(hass.bus.fire.called).to_be(True)
        expect(hass.bus.fire.mock_calls[0][1][0]).to_equal(folder_watcher.DOMAIN)
        expect(hass.bus.fire.mock_calls[0][1][1]).to_equal(
            {
                "event_type": "created",
                "path": "/hello/world.txt",
                "file": "world.txt",
                "folder": "/hello",
            }
        )


@test
def move_event() -> None:
    """Check that Home Assistant events are fired correctly on watchdog event."""

    class MockPatternMatchingEventHandler:
        """Mock base class for the pattern matcher event handler."""

        def __init__(self, patterns) -> None:
            pass

    with patch(
        "homeassistant.components.folder_watcher.PatternMatchingEventHandler",
        MockPatternMatchingEventHandler,
    ):
        hass = Mock()
        handler = folder_watcher.create_event_handler(["*"], hass, "1")
        handler.on_moved(
            SimpleNamespace(
                is_directory=False,
                src_path="/hello/world.txt",
                dest_path="/hello/earth.txt",
                event_type="moved",
            )
        )
        expect(hass.bus.fire.called).to_be(True)
        expect(hass.bus.fire.mock_calls[0][1][0]).to_equal(folder_watcher.DOMAIN)
        expect(hass.bus.fire.mock_calls[0][1][1]).to_equal(
            {
                "event_type": "moved",
                "path": "/hello/world.txt",
                "dest_path": "/hello/earth.txt",
                "file": "world.txt",
                "dest_file": "earth.txt",
                "folder": "/hello",
                "dest_folder": "/hello",
            }
        )
