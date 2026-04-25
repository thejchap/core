"""Tryke fixtures for the Hypontech Cloud tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from hyponcloud import AdminInfo, InverterData, OverviewData, PlantData
from tryke import Depends, fixture

from homeassistant.components.hypontech.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.hypontech.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
        unique_id="2123456789123456789",
    )


@fixture
def load_overview_fixture() -> OverviewData:
    """Load overview fixture data."""
    data = load_json_object_fixture("overview.json", DOMAIN)
    return OverviewData.from_dict(data["data"])


@fixture
def load_plant_list_fixture() -> list[PlantData]:
    """Load plant list fixture data."""
    data = load_json_object_fixture("plant_list.json", DOMAIN)
    return [PlantData.from_dict(item) for item in data["data"]]


@fixture
def load_inverters_fixture() -> list[InverterData]:
    """Load inverters fixture data."""
    data = load_json_object_fixture("inverters.json", DOMAIN)
    return [InverterData.from_dict(item) for item in data["data"]]


@fixture
def load_admin_info_fixture() -> AdminInfo:
    """Load admin info fixture data."""
    data = load_json_object_fixture("admin_info.json", DOMAIN)
    admin_data = data["data"]
    # Flatten nested "info" object into the main data dict
    if "info" in admin_data and isinstance(admin_data["info"], dict):
        info_data = admin_data.pop("info")
        admin_data.update(info_data)
    return AdminInfo.from_dict(admin_data)


@fixture
def mock_hyponcloud(
    overview: OverviewData = Depends(load_overview_fixture),
    plant_list: list[PlantData] = Depends(load_plant_list_fixture),
    inverters: list[InverterData] = Depends(load_inverters_fixture),
    admin_info: AdminInfo = Depends(load_admin_info_fixture),
) -> Generator[AsyncMock]:
    """Mock HyponCloud."""
    with (
        patch(
            "homeassistant.components.hypontech.HyponCloud", autospec=True
        ) as mock_hyponcloud,
        patch(
            "homeassistant.components.hypontech.config_flow.HyponCloud",
            new=mock_hyponcloud,
        ),
    ):
        mock_client = mock_hyponcloud.return_value
        mock_client.get_admin_info.return_value = admin_info
        mock_client.get_list.return_value = plant_list
        mock_client.get_overview.return_value = overview
        mock_client.get_inverters.return_value = inverters
        yield mock_client
