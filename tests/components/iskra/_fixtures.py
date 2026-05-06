"""Tryke fixtures for the iskra integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from .const import PQ_MODEL, SERIAL, SG_MODEL


class MockBasicInfo:
    """Mock BasicInfo class."""

    def __init__(self, model: str) -> None:
        """Initialize the mock class."""
        self.serial = SERIAL
        self.model = model
        self.description = "Iskra mock device"
        self.location = "imagination"
        self.sw_ver = "1.0.0"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.iskra.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_pyiskra_rest() -> Generator[MagicMock]:
    """Mock Iskra API authenticate with Rest API protocol."""
    with patch(
        "pyiskra.adapters.RestAPI.RestAPI.get_basic_info",
        return_value=MockBasicInfo(model=SG_MODEL),
    ) as basic_info_mock:
        yield basic_info_mock


@fixture
def mock_pyiskra_modbus() -> Generator[MagicMock]:
    """Mock Iskra API authenticate with Modbus protocol."""
    with patch(
        "pyiskra.adapters.Modbus.Modbus.get_basic_info",
        return_value=MockBasicInfo(model=PQ_MODEL),
    ) as basic_info_mock:
        yield basic_info_mock
