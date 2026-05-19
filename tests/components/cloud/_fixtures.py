"""Tryke fixtures for cloud tests."""

from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import DEFAULT, AsyncMock, MagicMock, PropertyMock, patch

from hass_nabucasa import Cloud, payments_api
from hass_nabucasa.auth import CognitoAuth
from hass_nabucasa.cloudhooks import Cloudhooks
from hass_nabucasa.const import DEFAULT_SERVERS, DEFAULT_VALUES, STATE_CONNECTED
from hass_nabucasa.files import Files
from hass_nabucasa.google_report_state import GoogleReportState
from hass_nabucasa.ice_servers import IceServers
from hass_nabucasa.iot import CloudIoT
from hass_nabucasa.remote import RemoteUI
from hass_nabucasa.voice import Voice
import jwt
from tryke import Depends, fixture

from homeassistant.components.cloud.client import CloudClient
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def load_homeassistant(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[None]:
    """Load the homeassistant integration.

    This is needed for the cloud integration to work.
    """
    assert await async_setup_component(hass, "homeassistant", {})
    yield


@fixture
def mock_user_data() -> Generator[MagicMock]:
    """Mock writing user info."""
    with patch("hass_nabucasa.Cloud._write_user_info") as writer:
        yield writer


@fixture
def mock_tts_cache_dir() -> Generator[None]:
    """Mock the TTS cache dir with empty dir."""
    with (
        patch(
            "homeassistant.components.tts._init_tts_cache_dir",
            return_value="/tmp/tts-cache",
        ),
        patch(
            "homeassistant.components.tts._get_cache_files",
            return_value={},
        ),
        patch(
            "homeassistant.components.tts.mutagen.File",
            create=True,
        ),
    ):
        yield


@fixture
async def cloud(
    _load_homeassistant: None = Depends(load_homeassistant),
    _mock_user_data: MagicMock = Depends(mock_user_data),
    _mock_tts_cache_dir: None = Depends(mock_tts_cache_dir),
) -> AsyncGenerator[MagicMock]:
    """Mock the cloud object.

    See the real hass_nabucasa.Cloud class for how to configure the mock.
    """
    with patch(
        "homeassistant.components.cloud.Cloud", autospec=True
    ) as mock_cloud_class:
        mock_cloud = mock_cloud_class.return_value

        # Attributes set in the constructor without parameters.
        mock_cloud.google_report_state = MagicMock(
            spec=GoogleReportState,
            request_sync=AsyncMock(),
        )
        mock_cloud.cloudhooks = MagicMock(spec=Cloudhooks)
        mock_cloud.remote = MagicMock(
            spec=RemoteUI,
            certificate=None,
            certificate_status=None,
            instance_domain=None,
            is_connected=False,
            latency_by_location={},
        )
        mock_cloud.auth = MagicMock(spec=CognitoAuth)
        mock_cloud.iot = MagicMock(
            spec=CloudIoT, last_disconnect_reason=None, state=STATE_CONNECTED
        )
        mock_cloud.voice = MagicMock(spec=Voice)
        mock_cloud.files = MagicMock(spec=Files)
        mock_cloud.started = None
        mock_cloud.payments = MagicMock(
            spec=payments_api.PaymentsApi,
            subscription_info=AsyncMock(),
            migrate_paypal_agreement=AsyncMock(),
        )
        mock_cloud.ice_servers = MagicMock(
            spec=IceServers,
            async_register_ice_servers_listener=AsyncMock(
                return_value=lambda: "mock-unregister"
            ),
        )
        mock_cloud.llm = MagicMock(async_ensure_token=AsyncMock())

        def set_up_mock_cloud(
            cloud_client: CloudClient, mode: str, **kwargs: Any
        ) -> DEFAULT:
            """Set up mock cloud with a mock constructor."""
            cloud_client.cloud = mock_cloud
            mock_cloud.client = cloud_client
            default_values = DEFAULT_VALUES[mode]
            servers = {
                f"{name}_server": server
                for name, server in DEFAULT_SERVERS[mode].items()
            }
            mock_cloud.configure_mock(**default_values, **servers)
            mock_cloud.configure_mock(**kwargs)
            mock_cloud.mode = mode

            # Properties that we mock as attributes from the constructor.
            mock_cloud.websession = cloud_client.websession

            return DEFAULT

        mock_cloud_class.side_effect = set_up_mock_cloud

        mock_cloud.id_token = None
        mock_cloud.access_token = None
        mock_cloud.refresh_token = None

        def mock_is_logged_in() -> bool:
            return mock_cloud.id_token is not None

        is_logged_in = PropertyMock(side_effect=mock_is_logged_in)
        type(mock_cloud).is_logged_in = is_logged_in

        def mock_claims() -> dict[str, Any]:
            return Cloud._decode_claims(mock_cloud.id_token)

        claims = PropertyMock(side_effect=mock_claims)
        type(mock_cloud).claims = claims

        def mock_is_connected() -> bool:
            return mock_cloud.iot.state == STATE_CONNECTED

        is_connected = PropertyMock(side_effect=mock_is_connected)
        type(mock_cloud).is_connected = is_connected
        type(mock_cloud.iot).connected = is_connected

        def mock_username() -> bool:
            return "abcdefghjkl"

        username = PropertyMock(side_effect=mock_username)
        type(mock_cloud).username = username

        mock_cloud.expiration_date = utcnow()
        mock_cloud.subscription_expired = False

        async def mock_login(
            email: str,
            password: str,
            *,
            check_connection: bool = False,
        ) -> None:
            """Mock login.

            When called, it should call the on_start callback.
            """
            mock_cloud.id_token = jwt.encode(
                {
                    "email": "hello@home-assistant.io",
                    "custom:sub-exp": "2018-01-03",
                    "cognito:username": "abcdefghjkl",
                },
                "test",
            )
            mock_cloud.access_token = "test_access_token"
            mock_cloud.refresh_token = "test_refresh_token"
            on_start_callback = mock_cloud.register_on_start.call_args[0][0]
            await on_start_callback()

        mock_cloud.login.side_effect = mock_login

        async def mock_logout() -> None:
            """Mock logout."""
            mock_cloud.id_token = None
            mock_cloud.access_token = None
            mock_cloud.refresh_token = None
            await mock_cloud.stop()
            await mock_cloud.client.logout_cleanups()

        mock_cloud.logout.side_effect = mock_logout

        yield mock_cloud
