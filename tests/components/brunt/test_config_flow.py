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

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

CONFIG = {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=None
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.brunt.config_flow.BruntClientAsync.async_login",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("test-username")
    expect(result2["data"]).to_equal(CONFIG)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_duplicate_login(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
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
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("server_disconnected", side_effect=ServerDisconnectedError, error_message="cannot_connect"),
    test.case("forbidden_403", side_effect=ClientResponseError(Mock(), None, status=403), error_message="invalid_auth"),
    test.case("unauthorized_401", side_effect=ClientResponseError(Mock(), None, status=401), error_message="unknown"),
    test.case("plain_exception", side_effect=Exception, error_message="unknown"),
)
async def form_error(
    side_effect,
    error_message: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle cannot connect."""
    with patch(
        "homeassistant.components.brunt.config_flow.BruntClientAsync.async_login",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=CONFIG
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": error_message})


@test.cases(
    test.case(
        "success",
        side_effect=None,
        result_type=FlowResultType.ABORT,
        password="test",
        step_id=None,
        reason="reauth_successful",
    ),
    test.case(
        "exception",
        side_effect=Exception,
        result_type=FlowResultType.FORM,
        password=CONFIG[CONF_PASSWORD],
        step_id="reauth_confirm",
        reason=None,
    ),
)
async def reauth(
    side_effect,
    result_type,
    password: str,
    step_id: str | None,
    reason: str | None,
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
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
    expect(result["type"]).to_be(FlowResultType.FORM)
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
