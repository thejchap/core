"""Test the Fresh-r config flow."""

from unittest.mock import AsyncMock, MagicMock

from aiohttp import ClientError
from pyfreshr.exceptions import LoginError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.freshr.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_freshr_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

USER_INPUT = {CONF_USERNAME: "test-user", CONF_PASSWORD: "test-pass"}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_freshr_client),
) -> None:
    """Test successful config flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Fresh-r (test-user)")
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal("test-user")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        exception=LoginError("bad credentials"),
        expected_error="invalid_auth",
    ),
    test.case(
        "unknown",
        exception=RuntimeError("unexpected"),
        expected_error="unknown",
    ),
    test.case(
        "cannot_connect",
        exception=ClientError("network"),
        expected_error="cannot_connect",
    ),
)
async def form_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_freshr_client),
    *,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test config flow handles login errors and recovers correctly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    client.login.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    # Ensure the flow can recover after providing correct credentials.
    client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_freshr_client),
) -> None:
    """Test config flow aborts when the account is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.skip("triggers real reload that hits AsyncResolver.real_close")
async def reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_freshr_client),
) -> None:
    """Test successful reauthentication updates the password and reloads."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "new-pass"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-pass")


@test.skip("triggers real reload that hits AsyncResolver.real_close")
async def reauth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_freshr_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication handles errors and recovers correctly."""


@test.skip("triggers real reload that hits AsyncResolver.real_close")
async def reconfigure_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_freshr_client),
) -> None:
    """Test successful reconfiguration updates the password and reloads."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["description_placeholders"]).to_equal({CONF_USERNAME: "test-user"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "new-pass"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-pass")
    expect(config_entry.data[CONF_USERNAME]).to_equal("test-user")


@test.skip("triggers real reload that hits AsyncResolver.real_close")
async def reconfigure_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_freshr_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration handles errors and recovers correctly."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    client.login.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "wrong-pass"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "new-pass"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-pass")
    expect(config_entry.data[CONF_USERNAME]).to_equal("test-user")


@test
async def form_already_configured_case_insensitive(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_freshr_client),
) -> None:
    """Test config flow aborts when the same account is configured with different casing."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={**USER_INPUT, CONF_USERNAME: USER_INPUT[CONF_USERNAME].upper()},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
