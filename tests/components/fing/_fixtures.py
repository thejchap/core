"""Tryke fixtures for Fing tests."""

from unittest.mock import MagicMock, patch

from fing_agent_api.models import AgentInfoResponse, DeviceResponse
from tryke import fixture

from homeassistant.components.fing.const import DOMAIN, UPNP_AVAILABLE
from homeassistant.const import CONF_API_KEY, CONF_IP_ADDRESS, CONF_PORT

from tests.common import (
    Generator,
    MockConfigEntry,
    load_fixture,
    load_json_object_fixture,
)


def make_mock_config_entry(api_type: str = "new") -> MockConfigEntry:
    """Return a mock config entry for the given api type."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_IP_ADDRESS: "192.168.1.1",
            CONF_PORT: "49090",
            CONF_API_KEY: "test_key",
            UPNP_AVAILABLE: api_type == "new",
        },
        unique_id="test_agent_id",
    )


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry (default api_type = new)."""
    return make_mock_config_entry("new")


def make_mocked_fing_agent(api_type: str = "new") -> Generator[MagicMock]:
    """Build a mocked FingAgent context manager generator."""
    with (
        patch(
            "homeassistant.components.fing.coordinator.FingAgent", autospec=True
        ) as mock_agent,
        patch("homeassistant.components.fing.config_flow.FingAgent", new=mock_agent),
    ):
        instance = mock_agent.return_value
        instance.get_devices.return_value = DeviceResponse(
            load_json_object_fixture(f"device_resp_{api_type}_API.json", DOMAIN)
        )
        instance.get_agent_info.return_value = AgentInfoResponse(
            load_fixture("agent_info_response.xml", DOMAIN)
        )
        yield instance


@fixture
def mocked_fing_agent() -> Generator[MagicMock]:
    """Mock a FingAgent instance with the default ('new') api type."""
    yield from make_mocked_fing_agent("new")
