"""The tests for local file init."""

from unittest.mock import MagicMock, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.file import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_is_allowed_path_true

from tests.common import MockConfigEntry, get_fixture_path
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def migration_to_version_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _allowed: MagicMock = Depends(mock_is_allowed_path_true),
) -> None:
    """Test the File sensor with JSON entries."""
    data = {
        "platform": "sensor",
        "name": "file2",
        "file_path": get_fixture_path("file_value_template.txt", "file"),
        "value_template": "{{ value_json.temperature }}",
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data=data,
        title=f"test [{data['file_path']}]",
    )
    entry.add_to_hass(hass)
    with (
        patch("os.path.isfile", Mock(return_value=True)),
        patch("os.access", Mock(return_value=True)),
    ):
        await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry.version).to_equal(2)
    expect(entry.data).to_equal(
        {
            "platform": "sensor",
            "name": "file2",
            "file_path": get_fixture_path("file_value_template.txt", "file"),
        }
    )
    expect(entry.options).to_equal(
        {"value_template": "{{ value_json.temperature }}"}
    )


@test
async def migration_from_future_version(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _allowed: MagicMock = Depends(mock_is_allowed_path_true),
) -> None:
    """Test the File sensor with future version migration."""
    data = {
        "platform": "sensor",
        "name": "file2",
        "file_path": get_fixture_path("file_value_template.txt", "file"),
        "value_template": "{{ value_json.temperature }}",
    }

    entry = MockConfigEntry(
        domain=DOMAIN, version=3, data=data, title=f"test [{data['file_path']}]"
    )
    entry.add_to_hass(hass)
    with (
        patch("os.path.isfile", Mock(return_value=True)),
        patch("os.access", Mock(return_value=True)),
    ):
        await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
