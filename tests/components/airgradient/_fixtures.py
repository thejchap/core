"""AirGradient test fixtures."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from airgradient import Config, Measures
from tryke import Depends, fixture

from homeassistant.components.airgradient.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry, load_fixture


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


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.airgradient.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_airgradient_client() -> Generator[AsyncMock]:
    """Mock an AirGradient client."""
    with (
        patch(
            "homeassistant.components.airgradient.AirGradientClient",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.airgradient.config_flow.AirGradientClient",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.host = "10.0.0.131"
        client.get_current_measures.return_value = Measures.from_json(
            load_fixture("current_measures_indoor.json", DOMAIN)
        )
        client.get_config.return_value = Config.from_json(
            load_fixture("get_config_local.json", DOMAIN)
        )
        client.get_latest_firmware_version.return_value = "3.1.4"
        yield client


@fixture
def mock_new_airgradient_client(
    mock_airgradient_client: AsyncMock = Depends(mock_airgradient_client),
) -> AsyncMock:
    """Mock a new AirGradient client."""
    mock_airgradient_client.get_config.return_value = Config.from_json(
        load_fixture("get_config.json", DOMAIN)
    )
    return mock_airgradient_client


@fixture
def mock_cloud_airgradient_client(
    mock_airgradient_client: AsyncMock = Depends(mock_airgradient_client),
) -> AsyncMock:
    """Mock a cloud AirGradient client."""
    mock_airgradient_client.get_config.return_value = Config.from_json(
        load_fixture("get_config_cloud.json", DOMAIN)
    )
    return mock_airgradient_client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Airgradient",
        data={CONF_HOST: "10.0.0.131"},
        unique_id="84fce612f5b8",
    )
