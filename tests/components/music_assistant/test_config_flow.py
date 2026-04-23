"""Define tests for the Music Assistant Integration config flow."""

from copy import deepcopy
from ipaddress import ip_address
from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

from music_assistant_client.exceptions import (
    CannotConnect,
    InvalidServerVersion,
    MusicAssistantClientException,
)
from music_assistant_models.api import ServerInfoMessage
from music_assistant_models.errors import AuthenticationFailed, InvalidToken
from tryke import Depends, expect, fixture, test

from homeassistant.components.music_assistant.config_flow import (
    CONF_URL,
    MusicAssistantConfigFlow,
    _get_server_info,
    _test_connection,
)
from homeassistant.components.music_assistant.const import (
    AUTH_SCHEMA_VERSION,
    CONF_TOKEN,
    DEFAULT_NAME,
    DOMAIN,
)
from homeassistant.config_entries import (
    SOURCE_HASSIO,
    SOURCE_IGNORE,
    SOURCE_REAUTH,
    SOURCE_USER,
    SOURCE_ZEROCONF,
    ConfigEntryState,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.hassio import HassioServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_async_zeroconf, mock_config_entry, mock_get_server_info

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network

SERVER_INFO = {
    "server_id": "1234",
    "base_url": "http://localhost:8095",
    "server_version": "0.0.0",
    "schema_version": AUTH_SCHEMA_VERSION,
    "min_supported_schema_version": AUTH_SCHEMA_VERSION,
    "homeassistant_addon": False,
    "onboard_done": True,
}

ZEROCONF_PROPERTIES = {
    "server_id": "1234",
    "base_url": "http://localhost:8095",
    "server_version": "0.0.0",
    "schema_version": str(AUTH_SCHEMA_VERSION),
    "min_supported_schema_version": str(AUTH_SCHEMA_VERSION),
    "homeassistant_addon": "False",
    "onboard_done": "True",
}

ZEROCONF_DATA = ZeroconfServiceInfo(
    ip_address=ip_address("127.0.0.1"),
    ip_addresses=[ip_address("127.0.0.1")],
    hostname="mock_hostname",
    port=None,
    type=mock.ANY,
    name=mock.ANY,
    properties=ZEROCONF_PROPERTIES,
)

HASSIO_DATA = HassioServiceInfo(
    config={"host": "addon-music-assistant", "port": 8094, "auth_token": "test_token"},
    name="Music Assistant",
    slug="music_assistant",
    uuid="1234",
)


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mgsi: AsyncMock = Depends(mock_get_server_info),
    _maz: MagicMock = Depends(mock_async_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test full flow with old schema (no auth required)."""
    server_info = ServerInfoMessage.from_json(
        await async_load_fixture(hass, "server_info_message.json", DOMAIN)
    )
    server_info.schema_version = AUTH_SCHEMA_VERSION - 1
    with patch(
        "homeassistant.components.music_assistant.config_flow._get_server_info",
        return_value=server_info,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_URL: "http://localhost:8095"},
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({CONF_URL: "http://localhost:8095"})
    expect(result["result"].unique_id).to_equal("1234")


@test
async def zeroconf_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test zeroconf flow with old schema (no auth required)."""
    old_schema_zeroconf_data = deepcopy(ZEROCONF_DATA)
    old_schema_zeroconf_data.properties["schema_version"] = AUTH_SCHEMA_VERSION - 1
    old_schema_zeroconf_data.properties["min_supported_schema_version"] = (
        AUTH_SCHEMA_VERSION - 1
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=old_schema_zeroconf_data,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({CONF_URL: "http://localhost:8095"})
    expect(result["result"].unique_id).to_equal("1234")


@test
async def zeroconf_invalid_discovery_info(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf flow with invalid discovery info."""
    bad_zeroconf_data = deepcopy(ZEROCONF_DATA)
    bad_zeroconf_data.properties.pop("server_id")
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=bad_zeroconf_data,
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_discovery_info")


@test
async def duplicate_user(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate user flow."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://localhost:8095"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def duplicate_zeroconf(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate zeroconf flow."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_server_version",
        InvalidServerVersion("invalid_server_version"),
        "invalid_server_version",
    ),
    test.case("cannot_connect", CannotConnect("cannot_connect"), "cannot_connect"),
    test.case("unknown", MusicAssistantClientException("unknown"), "unknown"),
)
async def flow_user_server_version_invalid(
    exception: MusicAssistantClientException,
    error_message: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mgsi: AsyncMock = Depends(mock_get_server_info),
) -> None:
    """Test user flow when server url is invalid."""
    mgsi.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://localhost:8095"},
    )
    await hass.async_block_till_done()
    expect(result["errors"]).to_equal({"base": error_message})

    mgsi.side_effect = None
    server_info = ServerInfoMessage.from_json(
        await async_load_fixture(hass, "server_info_message.json", DOMAIN)
    )
    server_info.schema_version = AUTH_SCHEMA_VERSION - 1
    mgsi.return_value = server_info

    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://localhost:8095"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_zeroconf_connect_issue(
    hass: HomeAssistant = Depends(hass_fixture),
    mgsi: AsyncMock = Depends(mock_get_server_info),
) -> None:
    """Test zeroconf flow when server connect be reached."""
    mgsi.side_effect = CannotConnect("cannot_connect")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def user_url_different_from_server_base_url(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that user-provided URL is used even when different from server base_url."""
    server_info = ServerInfoMessage.from_json(
        await async_load_fixture(hass, "server_info_message.json", DOMAIN)
    )
    server_info.base_url = "http://different-server:8095"
    server_info.schema_version = AUTH_SCHEMA_VERSION - 1
    with patch(
        "homeassistant.components.music_assistant.config_flow._get_server_info",
        return_value=server_info,
    ):
        user_url = "http://user-provided-server:8095"

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_URL: user_url},
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal({CONF_URL: user_url})
    expect(result["result"].unique_id).to_equal("1234")


@test
async def duplicate_user_with_different_urls(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test duplicate detection works with different user URLs."""
    existing_url = "http://existing-server:8095"
    existing_config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Music Assistant",
        data={CONF_URL: existing_url},
        unique_id="1234",
    )
    existing_config_entry.add_to_hass(hass)

    server_info = ServerInfoMessage.from_json(
        await async_load_fixture(hass, "server_info_message.json", DOMAIN)
    )
    server_info.base_url = "http://server-reported-url:8095"
    server_info.schema_version = AUTH_SCHEMA_VERSION - 1
    with patch(
        "homeassistant.components.music_assistant.config_flow._get_server_info",
        return_value=server_info,
    ):
        new_user_url = "http://new-user-url:8095"

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_URL: new_user_url},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_existing_entry_working_url(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf flow when existing entry has working URL."""
    entry.add_to_hass(hass)

    server_info = ServerInfoMessage.from_json(
        await async_load_fixture(hass, "server_info_message.json", DOMAIN)
    )
    server_info.base_url = "http://different-discovered-url:8095"
    server_info.schema_version = AUTH_SCHEMA_VERSION - 1
    with patch(
        "homeassistant.components.music_assistant.config_flow._get_server_info",
        return_value=server_info,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZEROCONF_DATA,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_URL]).to_equal("http://localhost:8095")


@test
async def zeroconf_existing_entry_ignored(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf flow when existing entry was ignored."""
    ignored_config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Music Assistant",
        data={},
        unique_id="1234",
        source=SOURCE_IGNORE,
    )
    ignored_config_entry.add_to_hass(hass)

    server_info = ServerInfoMessage.from_json(
        await async_load_fixture(hass, "server_info_message.json", DOMAIN)
    )
    server_info.base_url = "http://discovered-url:8095"
    server_info.schema_version = AUTH_SCHEMA_VERSION - 1
    with patch(
        "homeassistant.components.music_assistant.config_flow._get_server_info",
        return_value=server_info,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=ZEROCONF_DATA,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def hassio_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test hassio discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HASSIO},
        data=HASSIO_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("hassio_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_URL: "http://addon-music-assistant:8094",
            CONF_TOKEN: "test_token",
        }
    )
    expect(result["result"].unique_id).to_equal("1234")


@test
async def hassio_flow_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test hassio discovery flow with duplicate server."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HASSIO},
        data=HASSIO_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def hassio_flow_updates_failed_entry_and_reloads(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test hassio discovery updates entry in SETUP_ERROR state and schedules reload."""
    failed_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Music Assistant",
        data={CONF_URL: "http://old-url:8094", CONF_TOKEN: "old_token"},
        unique_id="1234",
    )
    failed_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.music_assistant.MusicAssistantClient"
    ) as mock_client:
        mock_client.return_value.connect.side_effect = AuthenticationFailed(
            "Invalid token"
        )
        await hass.config_entries.async_setup(failed_entry.entry_id)
        await hass.async_block_till_done()

    expect(failed_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    with patch.object(
        hass.config_entries, "async_schedule_reload"
    ) as mock_schedule_reload:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_HASSIO},
            data=HASSIO_DATA,
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")

        expect(failed_entry.data[CONF_URL]).to_equal("http://addon-music-assistant:8094")
        expect(failed_entry.data[CONF_TOKEN]).to_equal("test_token")

        mock_schedule_reload.assert_called_once_with(failed_entry.entry_id)


@test.cases(
    test.case(
        "invalid_server_version",
        InvalidServerVersion("invalid_server_version"),
        "invalid_server_version",
    ),
    test.case("cannot_connect", CannotConnect("cannot_connect"), "cannot_connect"),
    test.case("unknown", MusicAssistantClientException("unknown"), "unknown"),
)
async def hassio_flow_errors(
    exception: MusicAssistantClientException,
    error_reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mgsi: AsyncMock = Depends(mock_get_server_info),
) -> None:
    """Test hassio discovery flow with connection errors."""
    mgsi.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HASSIO},
        data=HASSIO_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error_reason)


@test
async def zeroconf_addon_server_ignored(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf discovery ignores servers running as add-on."""
    addon_zeroconf_data = deepcopy(ZEROCONF_DATA)
    addon_zeroconf_data.properties["homeassistant_addon"] = "True"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=addon_zeroconf_data,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_discovered_addon")


@test
async def zeroconf_old_schema_addon_not_ignored(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf discovery does NOT ignore add-on servers with old schema version."""
    old_schema_addon_data = deepcopy(ZEROCONF_DATA)
    old_schema_version = AUTH_SCHEMA_VERSION - 1
    old_schema_addon_data.properties["schema_version"] = str(old_schema_version)
    old_schema_addon_data.properties["min_supported_schema_version"] = str(
        old_schema_version
    )
    old_schema_addon_data.properties["homeassistant_addon"] = "True"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=old_schema_addon_data,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")


@test
async def user_flow_with_auth_required(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with schema >= 28 redirects to auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://localhost:8095"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth_manual")


@test
async def zeroconf_flow_with_auth_required(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf flow with schema >= 28 redirects to auth after confirmation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth_manual")


@test
async def hassio_flow_with_token(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test hassio discovery flow with token provided."""
    hassio_data_with_token = HassioServiceInfo(
        config={
            "host": "addon-music-assistant",
            "port": 8094,
            "auth_token": "test_token",
        },
        name="Music Assistant",
        slug="music_assistant",
        uuid="1234",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HASSIO},
        data=hassio_data_with_token,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("hassio_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_URL: "http://addon-music-assistant:8094",
            CONF_TOKEN: "test_token",
        }
    )
    expect(result["result"].unique_id).to_equal("1234")


@test
async def auth_flow_success(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test successful authentication flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://localhost:8095"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth_manual")

    with patch("homeassistant.components.music_assistant.config_flow._test_connection"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_TOKEN: "test_auth_token"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_URL: "http://localhost:8095",
            CONF_TOKEN: "test_auth_token",
        }
    )
    expect(result["result"].unique_id).to_equal("1234")


@test
async def finish_auth_token_exchange(
    hass: HomeAssistant = Depends(hass_fixture),
    mgsi: AsyncMock = Depends(mock_get_server_info),
) -> None:
    """Test that finish_auth exchanges short-lived token for long-lived token."""
    flow = MusicAssistantConfigFlow()
    flow.hass = hass
    flow.url = "http://localhost:8095"
    flow.token = "short_lived_session_token"
    flow.server_info = mgsi.return_value

    with patch(
        "homeassistant.components.music_assistant.config_flow.create_long_lived_token",
        return_value="long_lived_token_12345",
    ) as mock_create_token:
        result = await flow.async_step_finish_auth()

    mock_create_token.assert_called_once()
    call_args = mock_create_token.call_args
    expect(call_args[0][0]).to_equal("http://localhost:8095")
    expect(call_args[0][1]).to_equal("short_lived_session_token")
    expect(call_args[0][2]).to_equal("Home Assistant")
    expect(call_args[1]["aiohttp_session"]).not_.to_be(None)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_URL: "http://localhost:8095",
            CONF_TOKEN: "long_lived_token_12345",
        }
    )


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow shows confirmation before auth."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id},
        data=entry.data,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["description_placeholders"]["url"]).to_equal("http://localhost:8095")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth_manual")


@test
async def reauth_with_manual_token(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with manual token entry."""
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.music_assistant.config_flow._test_connection"
    ) as mock_test_connection:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id},
            data=entry.data,
        )
        expect(result["step_id"]).to_equal("reauth_confirm")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        expect(result["step_id"]).to_equal("auth_manual")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_TOKEN: "new_valid_token"},
        )

        mock_test_connection.assert_called_once_with(
            hass, "http://localhost:8095", "new_valid_token"
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")
        expect(entry.data[CONF_TOKEN]).to_equal("new_valid_token")


@test.cases(
    test.case("auth_failed", AuthenticationFailed("auth_failed"), "auth_failed"),
    test.case("invalid_token", InvalidToken("invalid_token"), "auth_failed"),
)
async def auth_manual_invalid_token(
    exception: Exception,
    error_key: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual auth with invalid token."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://localhost:8095"},
    )
    expect(result["step_id"]).to_equal("auth_manual")

    with patch(
        "homeassistant.components.music_assistant.config_flow._test_connection",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_TOKEN: "invalid_token"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth_manual")
    expect(result["errors"]).to_equal({"base": error_key})


@test.cases(
    test.case("cannot_connect", CannotConnect("cannot_connect"), "cannot_connect"),
    test.case(
        "invalid_server_version",
        InvalidServerVersion("invalid_server_version"),
        "invalid_server_version",
    ),
    test.case("unknown", MusicAssistantClientException("unknown"), "unknown"),
)
async def auth_manual_connection_errors(
    exception: Exception,
    abort_reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual auth with connection errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://localhost:8095"},
    )
    expect(result["step_id"]).to_equal("auth_manual")

    with patch(
        "homeassistant.components.music_assistant.config_flow._test_connection",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_TOKEN: "test_token"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(abort_reason)


@test
async def finish_auth_reauth_source(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test finish_auth updates entry when source is reauth."""
    entry.add_to_hass(hass)

    flow = MusicAssistantConfigFlow()
    flow.hass = hass
    flow.context = {"source": SOURCE_REAUTH, "entry_id": entry.entry_id}
    flow.url = "http://localhost:8095"
    flow.token = "session_token"

    with patch(
        "homeassistant.components.music_assistant.config_flow.create_long_lived_token",
        return_value="new_long_lived_token",
    ):
        result = await flow.async_step_finish_auth()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_TOKEN]).to_equal("new_long_lived_token")


@test.cases(
    test.case("timeout", TimeoutError(), "cannot_connect"),
    test.case("cannot_connect", CannotConnect("cannot_connect"), "cannot_connect"),
    test.case("auth_failed", AuthenticationFailed("auth_failed"), "auth_failed"),
    test.case("invalid_token", InvalidToken("invalid_token"), "auth_failed"),
    test.case(
        "invalid_version",
        InvalidServerVersion("invalid_version"),
        "invalid_server_version",
    ),
    test.case("unknown", MusicAssistantClientException("unknown"), "unknown"),
)
async def finish_auth_errors(
    exception: Exception,
    abort_reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test finish_auth handles errors during token exchange."""
    flow = MusicAssistantConfigFlow()
    flow.hass = hass
    flow.url = "http://localhost:8095"
    flow.token = "session_token"

    with patch(
        "homeassistant.components.music_assistant.config_flow.create_long_lived_token",
        side_effect=exception,
    ):
        result = await flow.async_step_finish_auth()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(abort_reason)


@test
async def auth_step_with_oauth2_callback(
    hass: HomeAssistant = Depends(hass_fixture),
    mgsi: AsyncMock = Depends(mock_get_server_info),
) -> None:
    """Test auth step receiving OAuth2 callback with code parameter."""
    flow = MusicAssistantConfigFlow()
    flow.hass = hass
    flow.url = "http://localhost:8095"
    flow.server_info = mgsi.return_value

    result = await flow.async_step_auth(user_input={"code": "test_session_token"})

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP_DONE)
    expect(result["step_id"]).to_equal("finish_auth")
    expect(flow.token).to_equal("test_session_token")


@test
async def auth_step_with_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mgsi: AsyncMock = Depends(mock_get_server_info),
) -> None:
    """Test auth step receiving error from OAuth2 callback."""
    flow = MusicAssistantConfigFlow()
    flow.hass = hass
    flow.url = "http://localhost:8095"
    flow.server_info = mgsi.return_value

    result = await flow.async_step_auth(user_input={"error": "access_denied"})

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("auth_error")


@test
async def get_server_info_helper(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test _get_server_info helper function."""
    expected_server_info = ServerInfoMessage.from_json(
        await async_load_fixture(hass, "server_info_message.json", DOMAIN)
    )

    with patch(
        "homeassistant.components.music_assistant.config_flow.get_server_info"
    ) as mock_lib_get_server_info:
        mock_lib_get_server_info.return_value = expected_server_info

        result = await _get_server_info(hass, "http://localhost:8095")

        expect(result).to_equal(expected_server_info)
        mock_lib_get_server_info.assert_called_once()


@test
async def test_connection_helper(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test _test_connection helper function."""
    with patch(
        "homeassistant.components.music_assistant.config_flow.MusicAssistantClient"
    ) as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        await _test_connection(hass, "http://localhost:8095", "test_token")

        mock_instance.send_command.assert_called_once_with("info")


@test
async def auth_with_redirect_uri(
    hass: HomeAssistant = Depends(hass_fixture),
    mgsi: AsyncMock = Depends(mock_get_server_info),
) -> None:
    """Test auth step with redirect URI available."""
    flow = MusicAssistantConfigFlow()
    flow.hass = hass
    flow.url = "http://localhost:8095"
    flow.flow_id = "test_flow_id"
    flow.server_info = mgsi.return_value

    with (
        patch(
            "homeassistant.components.music_assistant.config_flow.async_get_redirect_uri",
            return_value="http://localhost:8123/auth/external/callback",
        ),
        patch(
            "homeassistant.components.music_assistant.config_flow._encode_jwt",
            return_value="test_jwt_state",
        ),
    ):
        result = await flow.async_step_auth()

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["step_id"]).to_equal("auth")
    expect("http://localhost:8095/login" in result["url"]).to_be(True)
    expect(
        "return_url=http%3A%2F%2Flocalhost%3A8123%2Fauth%2Fexternal%2Fcallback%3Fstate%3Dtest_jwt_state"
        in result["url"]
    ).to_be(True)
    expect("device_name=Home+Assistant" in result["url"]).to_be(True)
