"""Test the YouTube config flow."""

from unittest.mock import patch

from youtubeaio.types import ForbiddenError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.youtube.const import CONF_CHANNELS, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from . import MockYouTube
from ._fixtures import (
    CLIENT_ID,
    GOOGLE_AUTH_URI,
    GOOGLE_TOKEN_URI,
    SCOPES,
    TITLE,
    ComponentSetup,
    mock_config_entry,
    mock_connection,
    setup_credentials,
    setup_integration,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth as hass_client_no_auth_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
    _connection: AiohttpClientMocker = Depends(mock_connection),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "youtube", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    with (
        patch(
            "homeassistant.components.youtube.async_setup_entry", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.youtube.config_flow.YouTube",
            return_value=MockYouTube(hass),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("channels")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]}
        )

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TITLE)
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("UC_x5XG1OV2P6uZZ5FSM9Ttw")
    expect("token" in result["result"].data).to_be(True)
    expect(result["result"].data["token"]["access_token"]).to_equal("mock-access-token")
    expect(result["result"].data["token"]["refresh_token"]).to_equal(
        "mock-refresh-token"
    )
    expect(result["options"]).to_equal({CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]})


@test
async def flow_abort_without_channel(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Check abort flow if user has no channel."""
    result = await hass.config_entries.flow.async_init(
        "youtube", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    service = MockYouTube(hass, channel_fixture="get_no_channel.json")
    with (
        patch("homeassistant.components.youtube.async_setup_entry", return_value=True),
        patch(
            "homeassistant.components.youtube.config_flow.YouTube", return_value=service
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_channel")


@test
async def flow_abort_without_subscriptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Check abort flow if user has no subscriptions and no own channel."""
    result = await hass.config_entries.flow.async_init(
        "youtube", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    service = MockYouTube(
        hass,
        channel_fixture="get_no_channel.json",
        subscriptions_fixture="get_no_subscriptions.json",
    )
    with (
        patch("homeassistant.components.youtube.async_setup_entry", return_value=True),
        patch(
            "homeassistant.components.youtube.config_flow.YouTube", return_value=service
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_channel")


@test
async def flow_without_subscriptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Check flow continues even without subscriptions since user has their own channel."""
    result = await hass.config_entries.flow.async_init(
        "youtube", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    service = MockYouTube(hass, subscriptions_fixture="get_no_subscriptions.json")
    with (
        patch("homeassistant.components.youtube.async_setup_entry", return_value=True),
        patch(
            "homeassistant.components.youtube.config_flow.YouTube", return_value=service
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("channels")

        # Verify the form schema contains only the user's own channel
        schema = result["data_schema"]
        channels = schema.schema[CONF_CHANNELS].config["options"]
        expect(len(channels)).to_equal(1)
        expect(channels[0]["value"]).to_equal("UC_x5XG1OV2P6uZZ5FSM9Ttw")
        expect("(Your Channel)" in channels[0]["label"]).to_be(True)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_http_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "youtube", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    msg = (
        "YouTube Data API v3 has not been used in project 0 before or it is "
        "disabled. Enable it by visiting "
        "https://console.developers.google.com/apis/api/youtube.googleapis.com/"
        "overview?project=0 then retry. If you enabled this API recently, wait a "
        "few minutes for the action to propagate to our systems and retry."
    )
    with patch(
        "homeassistant.components.youtube.config_flow.YouTube.get_user_channels",
        side_effect=ForbiddenError(msg),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("access_not_configured")
        expect(result["description_placeholders"]["message"]).to_equal(msg)


@test.cases(
    test.case(
        "successful",
        fixture_name="get_channel",
        abort_reason="reauth_successful",
        placeholders=None,
        call_count=1,
        access_token="updated-access-token",
    ),
    test.case(
        "wrong_account",
        fixture_name="get_channel_2",
        abort_reason="wrong_account",
        placeholders={"title": "Linus Tech Tips"},
        call_count=0,
        access_token="mock-access-token",
    ),
)
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    fixture_name: str,
    abort_reason: str,
    placeholders: dict[str, str] | None,
    call_count: int,
    access_token: str,
) -> None:
    """Test the re-authentication case updates the correct config entry."""
    config_entry.add_to_hass(hass)

    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    result = flows[0]
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    youtube = MockYouTube(hass, channel_fixture=f"{fixture_name}.json")
    with (
        patch(
            "homeassistant.components.youtube.async_setup_entry", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.youtube.config_flow.YouTube",
            return_value=youtube,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(abort_reason)
    expect(result["description_placeholders"]).to_equal(placeholders)
    expect(len(mock_setup.mock_calls)).to_equal(call_count)

    expect(config_entry.unique_id).to_equal("UC_x5XG1OV2P6uZZ5FSM9Ttw")
    expect("token" in config_entry.data).to_be(True)
    expect(config_entry.data["token"]["access_token"]).to_equal(access_token)
    expect(config_entry.data["token"]["refresh_token"]).to_equal("mock-refresh-token")


@test
async def flow_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "youtube", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    with patch(
        "homeassistant.components.youtube.config_flow.YouTube", side_effect=Exception
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("unknown")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: ComponentSetup = Depends(setup_integration),
) -> None:
    """Test the full options flow."""
    await setup()
    with patch(
        "homeassistant.components.youtube.config_flow.YouTube",
        return_value=MockYouTube(hass),
    ):
        entry = hass.config_entries.async_entries(DOMAIN)[0]
        result = await hass.config_entries.options.async_init(entry.entry_id)
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]},
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal({CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]})


@test
async def own_channel_included(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> None:
    """Test that the user's own channel is included in the list of selectable channels."""
    result = await hass.config_entries.flow.async_init(
        "youtube", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    with (
        patch(
            "homeassistant.components.youtube.async_setup_entry", return_value=True
        ),
        patch(
            "homeassistant.components.youtube.config_flow.YouTube",
            return_value=MockYouTube(hass),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("channels")

        schema = result["data_schema"]
        channels = schema.schema[CONF_CHANNELS].config["options"]
        has_own_channel = any(
            channel["value"] == "UC_x5XG1OV2P6uZZ5FSM9Ttw"
            and "(Your Channel)" in channel["label"]
            for channel in channels
        )
        expect(has_own_channel).to_be(True)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw", "UC_x5XG1OV2P6uZZ5FSM9Ttw"]
            },
        )

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def options_flow_own_channel(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: ComponentSetup = Depends(setup_integration),
) -> None:
    """Test the options flow includes the user's own channel."""
    await setup()
    with patch(
        "homeassistant.components.youtube.config_flow.YouTube",
        return_value=MockYouTube(hass),
    ):
        entry = hass.config_entries.async_entries(DOMAIN)[0]
        result = await hass.config_entries.options.async_init(entry.entry_id)
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        schema = result["data_schema"]
        channels = schema.schema[CONF_CHANNELS].config["options"]
        has_own_channel = any(
            channel["value"] == "UC_x5XG1OV2P6uZZ5FSM9Ttw"
            and "(Your Channel)" in channel["label"]
            for channel in channels
        )
        expect(has_own_channel).to_be(True)

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]},
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal({CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]})
