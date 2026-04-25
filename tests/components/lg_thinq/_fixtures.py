"""Tryke fixtures for the LGThinQ integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from thinqconnect import ThinQAPIException
from tryke import Depends, fixture

from homeassistant.components.lg_thinq.const import CONF_CONNECT_CLIENT_ID, DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_COUNTRY

from .const import MOCK_CONNECT_CLIENT_ID, MOCK_COUNTRY, MOCK_PAT, MOCK_UUID

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Test {DOMAIN}",
        unique_id=MOCK_PAT,
        data={
            CONF_ACCESS_TOKEN: MOCK_PAT,
            CONF_CONNECT_CLIENT_ID: MOCK_CONNECT_CLIENT_ID,
            CONF_COUNTRY: MOCK_COUNTRY,
        },
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.lg_thinq.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_uuid() -> Generator[AsyncMock]:
    """Mock a uuid."""
    with (
        patch("uuid.uuid4", autospec=True, return_value=MOCK_UUID) as mock_uuid,
        patch(
            "homeassistant.components.lg_thinq.config_flow.uuid.uuid4",
            new=mock_uuid,
        ),
    ):
        yield mock_uuid.return_value


@fixture
def mock_config_thinq_api() -> Generator[AsyncMock]:
    """Mock a thinq api."""
    with (
        patch("homeassistant.components.lg_thinq.ThinQApi", autospec=True) as mock_api,
        patch(
            "homeassistant.components.lg_thinq.config_flow.ThinQApi",
            new=mock_api,
        ),
    ):
        thinq_api = mock_api.return_value
        thinq_api.async_get_device_list.return_value = ["air_conditioner"]
        yield thinq_api


@fixture
def mock_invalid_thinq_api(
    mock_config_thinq_api: AsyncMock = Depends(mock_config_thinq_api),
) -> AsyncMock:
    """Mock an invalid thinq api."""
    mock_config_thinq_api.async_get_device_list = AsyncMock(
        side_effect=ThinQAPIException(
            code="1309", message="Not allowed api call", headers=None
        )
    )
    return mock_config_thinq_api
