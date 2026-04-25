"""Tryke fixtures for the TOLO Sauna config flow tests."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import fixture

from homeassistant.components.tolo.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry


@fixture
def toloclient() -> Generator[Mock]:
    """Patch libraries."""
    with patch("homeassistant.components.tolo.config_flow.ToloClient") as toloclient:
        yield toloclient


@fixture
def coordinator_toloclient() -> Generator[Mock]:
    """Patch ToloClient in async_setup_entry to abort entry setup."""
    with patch(
        "homeassistant.components.tolo.coordinator.ToloClient", side_effect=Exception
    ) as toloclient:
        yield toloclient


@fixture
def config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="TOLO Steam Bath",
        entry_id="1",
        data={
            CONF_HOST: "127.0.0.1",
        },
    )
