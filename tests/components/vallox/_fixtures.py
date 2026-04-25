"""Tryke fixtures for Vallox tests."""

from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture
from vallox_websocket_api import MetricData

from homeassistant.components.vallox.const import DOMAIN
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

DEFAULT_HOST = "192.168.100.50"
DEFAULT_NAME = "Vallox"


def create_mock_entry(hass: HomeAssistant, host: str, name: str) -> MockConfigEntry:
    """Create mocked Vallox config entry."""
    vallox_mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: host,
            CONF_NAME: name,
        },
    )
    vallox_mock_entry.add_to_hass(hass)

    return vallox_mock_entry


async def do_setup_vallox_entry(hass: HomeAssistant, host: str, name: str) -> None:
    """Set up the Vallox component."""
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            CONF_HOST: host,
            CONF_NAME: name,
        },
    )
    await hass.async_block_till_done()


@fixture
def default_metrics() -> dict[str, int]:
    """Return default Vallox metrics."""
    return {
        "A_CYC_MACHINE_MODEL": 3,
        "A_CYC_APPL_SW_VERSION_1": 2,
        "A_CYC_APPL_SW_VERSION_2": 0,
        "A_CYC_APPL_SW_VERSION_3": 16,
        "A_CYC_UUID0": 5,
        "A_CYC_UUID1": 6,
        "A_CYC_UUID2": 7,
        "A_CYC_UUID3": 8,
        "A_CYC_UUID4": 9,
        "A_CYC_UUID5": 10,
        "A_CYC_UUID6": 11,
        "A_CYC_UUID7": 12,
        "A_CYC_BOOST_TIMER": 0,
        "A_CYC_FIREPLACE_TIMER": 0,
        "A_CYC_EXTRA_TIMER": 0,
        "A_CYC_MODE": 0,
        "A_CYC_STATE": 0,
        "A_CYC_FILTER_CHANGED_YEAR": 24,
        "A_CYC_FILTER_CHANGED_MONTH": 2,
        "A_CYC_FILTER_CHANGED_DAY": 16,
        "A_CYC_FILTER_CHANGE_INTERVAL": 120,
        "A_CYC_TOTAL_FAULT_COUNT": 0,
        "A_CYC_FAULT_CODE": 0,
        "A_CYC_FAULT_ACTIVITY": 0,
        "A_CYC_FAULT_FIRST_DATE": 0,
        "A_CYC_FAULT_LAST_DATE": 0,
        "A_CYC_FAULT_SEVERITY": 0,
        "A_CYC_FAULT_COUNT": 0,
        "A_CYC_HOME_SPEED_SETTING": 30,
        "A_CYC_AWAY_SPEED_SETTING": 10,
        "A_CYC_BOOST_SPEED_SETTING": 80,
    }


@fixture
def fetch_metric_data_mock(
    metrics: dict[str, int] = Depends(default_metrics),
) -> Any:
    """Stub the Vallox fetch_metric_data method."""
    with patch(
        "homeassistant.components.vallox.Vallox.fetch_metric_data",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = MetricData(metrics)
        yield mock


@fixture
def mock_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Create mocked Vallox config entry fixture."""
    return create_mock_entry(hass, DEFAULT_HOST, DEFAULT_NAME)


@fixture
async def setup_vallox_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _metrics_mock: Any = Depends(fetch_metric_data_mock),
) -> None:
    """Define a fixture to set up Vallox."""
    await do_setup_vallox_entry(hass, DEFAULT_HOST, DEFAULT_NAME)


@fixture
async def init_reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_entry),
    _setup: None = Depends(setup_vallox_entry),
) -> tuple[MockConfigEntry, ConfigFlowResult]:
    """Initialize a config entry and a reconfigure flow for it."""
    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Original entry.
    assert entry.data["host"] == "192.168.100.50"

    return (entry, result)
