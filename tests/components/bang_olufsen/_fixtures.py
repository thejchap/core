"""Tryke fixtures for Bang & Olufsen."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

from mozart_api.models import (
    BeolinkSelf,
    PlaybackContentMetadata,
    PlaybackProgress,
    PlaybackState,
    ProductState,
    RenderingState,
    SoftwareUpdateState,
    SoftwareUpdateStatus,
    Source,
    VolumeState,
)
from tryke import fixture

from .const import TEST_FRIENDLY_NAME, TEST_JID_1


@fixture
def mock_mozart_client() -> Generator[AsyncMock]:
    """Mock MozartClient (minimal for config flow tests)."""
    with (
        patch(
            "homeassistant.components.bang_olufsen.MozartClient", autospec=True
        ) as mock_client,
        patch(
            "homeassistant.components.bang_olufsen.config_flow.MozartClient",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value

        client.get_beolink_self = AsyncMock()
        client.get_beolink_self.return_value = BeolinkSelf(
            friendly_name=TEST_FRIENDLY_NAME, jid=TEST_JID_1
        )
        client.get_softwareupdate_status = AsyncMock()
        client.get_softwareupdate_status.return_value = SoftwareUpdateStatus(
            software_version="1.0.0", state=SoftwareUpdateState()
        )
        client.get_product_state = AsyncMock()
        client.get_product_state.return_value = ProductState(
            volume=VolumeState(),
            playback=PlaybackState(
                metadata=PlaybackContentMetadata(),
                progress=PlaybackProgress(),
                source=Source(),
                state=RenderingState(value="started"),
            ),
        )

        client.check_device_connection = AsyncMock()
        client.close_api_client = AsyncMock()
        client.connect_notifications = AsyncMock()
        client.disconnect_notifications = Mock()
        client.websocket_connected = False

        yield client


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock successful setup entry."""
    with patch(
        "homeassistant.components.bang_olufsen.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
