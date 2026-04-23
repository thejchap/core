"""Tryke fixtures for emoncms."""

from collections.abc import AsyncGenerator, Generator
import copy
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.emoncms.const import CONF_ONLY_INCLUDE_FEEDID, DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_URL

from tests.common import MockConfigEntry

UNITS = ["kWh", "Wh", "W", "V", "A", "VA", "°C", "°F", "K", "Hz", "hPa", ""]


def get_feed(
    number: int, unit: str = "W", value: float = 18.04, timestamp: int = 1665509570
):
    """Generate feed details."""
    return {
        "id": str(number),
        "userid": "1",
        "name": f"parameter {number}",
        "tag": "tag",
        "size": "35809224",
        "unit": unit,
        "time": timestamp,
        "value": value,
    }


FEEDS = [get_feed(i + 1, unit=unit) for i, unit in enumerate(UNITS)]

EMONCMS_FAILURE = {"success": False, "message": "failure"}

FLOW_RESULT = {
    CONF_API_KEY: "my_api_key",
    CONF_ONLY_INCLUDE_FEEDID: [str(i + 1) for i in range(len(UNITS))],
    CONF_URL: "http://1.1.1.1",
}

SENSOR_NAME = "emoncms@1.1.1.1"
UNIQUE_ID = "123-53535292"


@fixture
def config_entry() -> MockConfigEntry:
    """Mock emoncms config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=SENSOR_NAME,
        data=FLOW_RESULT,
    )


FLOW_RESULT_SECOND_URL = copy.deepcopy(FLOW_RESULT)
FLOW_RESULT_SECOND_URL[CONF_URL] = "http://1.1.1.2"


@fixture
def config_entry_unique_id() -> MockConfigEntry:
    """Mock emoncms config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=SENSOR_NAME,
        data=FLOW_RESULT_SECOND_URL,
        unique_id=UNIQUE_ID,
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.emoncms.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def emoncms_client() -> AsyncGenerator[AsyncMock]:
    """Mock pyemoncms success response."""
    with (
        patch(
            "homeassistant.components.emoncms.EmoncmsClient", autospec=True
        ) as mock_client,
        patch(
            "homeassistant.components.emoncms.config_flow.EmoncmsClient",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.async_request.return_value = {"success": True, "message": FEEDS}
        client.async_get_uuid.return_value = UNIQUE_ID
        yield client


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc
