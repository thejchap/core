"""Test the Google Mail config flow."""

from unittest.mock import patch

from httplib2 import Response
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.google_mail.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    CLIENT_ID,
    GOOGLE_AUTH_URI,
    SCOPES,
    TITLE,
    config_entry,
    mock_connection,
    setup_credentials,
)

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import (
    ClientSessionGenerator,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _creds: None = Depends(setup_credentials),
    _conn: None = Depends(mock_connection),
    _request: None = Depends(current_request_with_host),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def full_flow(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "google_mail", context={"source": config_entries.SOURCE_USER}
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

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    with (
        patch(
            "homeassistant.components.google_mail.async_setup_entry", return_value=True
        ) as mock_setup,
        patch(
            "httplib2.Http.request",
            return_value=(
                Response({}),
                bytes(
                    await async_load_fixture(hass, "get_profile.json", DOMAIN),
                    encoding="UTF-8",
                ),
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(TITLE)
    expect("result" in result).to_be(True)
    expect(result.get("result").unique_id).to_equal(TITLE)
    expect("token" in result.get("result").data).to_be(True)
    expect(result.get("result").data["token"].get("access_token")).to_equal(
        "mock-access-token"
    )
    expect(result.get("result").data["token"].get("refresh_token")).to_equal(
        "mock-refresh-token"
    )


@test
async def already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test case where config flow discovers unique id was already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        "google_mail", context={"source": config_entries.SOURCE_USER}
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

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    with patch(
        "httplib2.Http.request",
        return_value=(
            Response({}),
            bytes(
                await async_load_fixture(hass, "get_profile.json", DOMAIN),
                encoding="UTF-8",
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test.skip("multi-parametrize reauth flow needs more work")
async def reauth(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the re-authentication case updates the correct config entry."""
