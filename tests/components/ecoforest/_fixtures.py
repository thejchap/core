"""Common fixtures for the Ecoforest tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

from pyecoforest.models.device import Alarm, Device, OperationMode, State
from tryke import Depends, fixture

from homeassistant.components.ecoforest.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ecoforest.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def config() -> dict[str, str]:
    """Define a config entry data fixture."""
    return {
        CONF_HOST: "1.1.1.1",
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
    }


@fixture
def serial_number() -> str:
    """Define a serial number fixture."""
    return "1234"


@fixture
def mock_device(serial_number: str = Depends(serial_number)) -> Mock:
    """Define a mocked Ecoforest device fixture."""
    mock = Mock(spec=Device)
    mock.model = "model-version"
    mock.model_name = "model-name"
    mock.firmware = "firmware-version"
    mock.serial_number = serial_number
    mock.operation_mode = OperationMode.POWER
    mock.on = False
    mock.state = State.OFF
    mock.power = 3
    mock.temperature = 21.5
    mock.alarm = Alarm.PELLETS
    mock.alarm_code = "A099"
    mock.environment_temperature = 23.5
    mock.cpu_temperature = 36.1
    mock.gas_temperature = 40.2
    mock.ntc_temperature = 24.2
    return mock


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass),
    config: dict[str, str] = Depends(config),
    serial_number: str = Depends(serial_number),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="45a36e55aaddb2007c5f6602e0c38e72",
        title=f"Ecoforest {serial_number}",
        unique_id=serial_number,
        data=config,
    )
    entry.add_to_hass(hass)
    return entry
