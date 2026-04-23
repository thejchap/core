"""Test the Brunt config flow."""

from unittest.mock import AsyncMock, Mock, patch

from aiohttp import ClientResponseError
from aiohttp.client_exceptions import ServerDisconnectedError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.brunt.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.brunt._fixtures import mock_setup_entry
from tests.hass_fixtures import hass, mock_network

CONFIG = {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=None
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    with patch(
        "homeassistant.components.brunt.config_flow.BruntClientAsync.async_login",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )
        await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("test-username")
    expect(result2["data"]).to_equal(CONFIG)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_duplicate_login(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test uniqueness of username."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG,
        title="test-username",
        unique_id="test-username",
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.brunt.config_flow.BruntClientAsync.async_login",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=CONFIG
        )
        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("server_disconnected", ServerDisconnectedError, "cannot_connect"),
    test.case(
        "http_403", ClientResponseError(Mock(), None, status=403), "invalid_auth"
    ),
    test.case("http_401", ClientResponseError(Mock(), None, status=401), "unknown"),
    test.case("exception", Exception, "unknown"),
)
async def form_error(
    side_effect: type[Exception] | Exception,
    error_message: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect."""
    with patch(
        "homeassistant.components.brunt.config_flow.BruntClientAsync.async_login",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=CONFIG
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal({"base": error_message})


@test.cases(
    test.case(
        "success", None, FlowResultType.ABORT, "test", None, "reauth_successful"
    ),
    test.case(
        "exception",
        Exception,
        FlowResultType.FORM,
        CONFIG[CONF_PASSWORD],
        "reauth_confirm",
        None,
    ),
)
async def reauth(
    side_effect: type[Exception] | None,
    result_type: FlowResultType,
    password: str,
    step_id: str | None,
    reason: str | None,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test uniqueness of username."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG,
        title="test-username",
        unique_id="test-username",
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")
    with patch(
        "homeassistant.components.brunt.config_flow.BruntClientAsync.async_login",
        return_value=None,
        side_effect=side_effect,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"password": "test"},
        )
        expect(result3["type"]).to_equal(result_type)
        expect(entry.data["password"]).to_equal(password)
        expect(result3.get("step_id", None)).to_equal(step_id)
        expect(result3.get("reason", None)).to_equal(reason)
