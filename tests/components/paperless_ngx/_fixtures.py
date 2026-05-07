"""Tryke fixtures for the paperless_ngx integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from pypaperless.models import RemoteVersion, Statistic, Status
from tryke import Depends, fixture

from homeassistant.components.paperless_ngx.const import DOMAIN

from .const import USER_INPUT_ONE

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_status_data() -> dict:
    """Return test status data."""
    return load_json_object_fixture("test_data_status.json", DOMAIN)


@fixture
def mock_remote_version_data() -> dict:
    """Return test remote version data."""
    return load_json_object_fixture("test_data_remote_version.json", DOMAIN)


@fixture
def mock_statistic_data() -> dict:
    """Return test statistic data."""
    return load_json_object_fixture("test_data_statistic.json", DOMAIN)


@fixture
def mock_paperless(
    statistic_data: dict = Depends(mock_statistic_data),
    status_data: dict = Depends(mock_status_data),
    remote_version_data: dict = Depends(mock_remote_version_data),
) -> Generator[AsyncMock]:
    """Mock the pypaperless.Paperless client."""
    with (
        patch(
            "homeassistant.components.paperless_ngx.coordinator.Paperless",
            autospec=True,
        ) as paperless_mock,
        patch(
            "homeassistant.components.paperless_ngx.config_flow.Paperless",
            new=paperless_mock,
        ),
        patch(
            "homeassistant.components.paperless_ngx.Paperless",
            new=paperless_mock,
        ),
    ):
        paperless = paperless_mock.return_value

        paperless.base_url = "http://paperless.example.com/"
        paperless.host_version = "2.3.0"
        paperless.initialize.return_value = None
        paperless.statistics = AsyncMock(
            return_value=Statistic.create_with_data(
                paperless, data=statistic_data, fetched=True
            )
        )
        paperless.status = AsyncMock(
            return_value=Status.create_with_data(
                paperless, data=status_data, fetched=True
            )
        )
        paperless.remote_version = AsyncMock(
            return_value=RemoteVersion.create_with_data(
                paperless, data=remote_version_data, fetched=True
            )
        )

        yield paperless


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        entry_id="0KLG00V55WEVTJ0CJHM0GADNGH",
        title="Paperless-ngx",
        domain=DOMAIN,
        data=USER_INPUT_ONE,
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.paperless_ngx.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
