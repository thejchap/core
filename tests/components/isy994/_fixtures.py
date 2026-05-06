"""Tryke fixtures for the ISY994 integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.isy994.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_UUID = "00:00:00:00:00:00"


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "http://1.1.1.1",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
        unique_id=MOCK_UUID,
    )


@fixture
def mock_isy() -> MagicMock:
    """Return a mock ISY object."""
    mock = MagicMock()
    mock.nodes = MagicMock()
    mock.nodes.__iter__.return_value = []
    mock.nodes.status_events = MagicMock()
    mock.programs = MagicMock()
    mock.programs.get_by_name.return_value = None
    mock.variables = MagicMock()
    mock.variables.children = []
    mock.networking = MagicMock()
    mock.networking.nobjs = []
    mock.clock = MagicMock()
    mock.websocket = MagicMock()
    mock.conf = {
        "name": "Skynet ISY",
        "model": "IoX",
        "firmware": "6.0.4",
        "Networking Module": True,
        "Portal": True,
    }
    mock.uuid = MOCK_UUID
    mock.conn.url = "http://1.1.1.1:80"
    mock.initialize = AsyncMock()
    return mock


@fixture
def mock_isy_init(
    mock_isy: MagicMock = Depends(mock_isy),
) -> Generator[MagicMock]:
    """Mock pyisy.ISY initialization."""
    with (
        patch("homeassistant.components.isy994.ISY", return_value=mock_isy),
        patch(
            "homeassistant.components.isy994.config_flow.Connection.test_connection",
            return_value="<configuration></configuration>",
        ),
    ):
        yield mock_isy
