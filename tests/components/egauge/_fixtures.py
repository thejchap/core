"""Tryke fixtures for eGauge integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from egauge_async.json.models import RegisterInfo, RegisterType
from tryke import fixture

from homeassistant.components.egauge.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="eGauge",
        domain=DOMAIN,
        data={
            CONF_HOST: "http://192.168.1.100",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        },
        unique_id="ABC123456",
    )


@fixture
def mock_egauge_client() -> Generator[MagicMock]:
    """Return a mocked eGauge client."""
    with (
        patch(
            "homeassistant.components.egauge.coordinator.EgaugeJsonClient",
            autospec=True,
        ) as mock_class,
        patch(
            "homeassistant.components.egauge.config_flow.EgaugeJsonClient",
            new=mock_class,
        ),
    ):
        client = mock_class.return_value

        client.get_device_serial_number.return_value = "ABC123456"
        client.get_hostname.return_value = "egauge-home"
        client.get_register_info.return_value = {
            "Grid": RegisterInfo(name="Grid", type=RegisterType.POWER, idx=0, did=None),
            "Solar": RegisterInfo(
                name="Solar", type=RegisterType.POWER, idx=1, did=None
            ),
            "Temp": RegisterInfo(
                name="Temp", type=RegisterType.TEMPERATURE, idx=2, did=None
            ),
            "L1": RegisterInfo(name="L1", type=RegisterType.VOLTAGE, idx=3, did=None),
            "S1": RegisterInfo(name="S1", type=RegisterType.CURRENT, idx=4, did=None),
        }

        client.get_current_measurements.return_value = {
            "Grid": 1500.0,
            "Solar": -2500.0,
            "Temp": 45.0,
            "L1": 123.4,
            "S1": 1.2,
        }
        client.get_current_counters.return_value = {
            "Grid": 450000000.0,
            "Solar": 315000000.0,
            "Temp": 0.0,
            "L1": 12345678.0,
            "S1": 12345.0,
        }

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
