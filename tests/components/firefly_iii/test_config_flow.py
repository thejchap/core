"""Test the Firefly III config flow."""

from unittest.mock import AsyncMock, MagicMock

from pyfirefly.exceptions import (
    FireflyAuthenticationError,
    FireflyConnectionError,
    FireflyTimeoutError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.firefly_iii.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    MOCK_TEST_CONFIG,
    mock_config_entry,
    mock_firefly_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_USER_SETUP = {
    CONF_URL: "https://127.0.0.1:8080/",
    CONF_API_KEY: "test_api_key",
    CONF_VERIFY_SSL: True,
}

USER_INPUT_RECONFIGURE = {
    CONF_URL: "https://new_domain:9000/",
    CONF_API_KEY: "new_api_key",
    CONF_VERIFY_SSL: True,
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def form_and_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_firefly_client),
    _setup_entry: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form and can complete the flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("https://127.0.0.1:8080/")
    expect(result["data"]).to_equal(MOCK_TEST_CONFIG)


@test.cases(
    test.case(
        "invalid_auth", exception=FireflyAuthenticationError, reason="invalid_auth"
    ),
    test.case(
        "cannot_connect", exception=FireflyConnectionError, reason="cannot_connect"
    ),
    test.case(
        "timeout_connect", exception=FireflyTimeoutError, reason="timeout_connect"
    ),
    test.case("unknown", exception=Exception("Some other error"), reason="unknown"),
)
async def form_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_firefly_client),
    _setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    reason: str,
) -> None:
    """Test we handle all exceptions."""
    client.get_about.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    client.get_about.side_effect = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("https://127.0.0.1:8080/")
    expect(result["data"]).to_equal(MOCK_TEST_CONFIG)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_firefly_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle duplicate entries."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def full_flow_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_firefly_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the full flow of the config flow."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("new_api_key")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth", exception=FireflyAuthenticationError, reason="invalid_auth"
    ),
    test.case(
        "cannot_connect", exception=FireflyConnectionError, reason="cannot_connect"
    ),
    test.case(
        "timeout_connect", exception=FireflyTimeoutError, reason="timeout_connect"
    ),
    test.case("unknown", exception=Exception("Some other error"), reason="unknown"),
)
async def reauth_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_firefly_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    reason: str,
) -> None:
    """Test we handle all exceptions in the reauth flow."""
    config_entry.add_to_hass(hass)
    client.get_about.side_effect = exception

    await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    client.get_about.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("new_api_key")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def full_flow_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_firefly_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the full flow of the config flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("new_api_key")
    expect(config_entry.data[CONF_URL]).to_equal("https://new_domain:9000/")
    expect(config_entry.data[CONF_VERIFY_SSL]).to_be(True)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def full_flow_reconfigure_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_firefly_client),
    _setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the full flow of the config flow, this time with a known unique ID."""
    config_entry.add_to_hass(hass)
    duplicate_entry = MockConfigEntry(
        domain="firefly_iii",
        data={
            CONF_URL: "https://duplicate-url/",
            CONF_API_KEY: "other_key",
            CONF_VERIFY_SSL: True,
        },
        unique_id="very-annoying-duplicate",
    )
    duplicate_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_URL: "https://duplicate-url/",
            CONF_API_KEY: "new_key",
            CONF_VERIFY_SSL: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_auth", exception=FireflyAuthenticationError, reason="invalid_auth"
    ),
    test.case(
        "cannot_connect", exception=FireflyConnectionError, reason="cannot_connect"
    ),
    test.case(
        "timeout_connect", exception=FireflyTimeoutError, reason="timeout_connect"
    ),
    test.case("unknown", exception=Exception("Some other error"), reason="unknown"),
)
async def full_flow_reconfigure_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_firefly_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    reason: str,
) -> None:
    """Test the full flow of the config flow, this time with exceptions."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    client.get_about.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    client.get_about.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("new_api_key")
    expect(config_entry.data[CONF_URL]).to_equal("https://new_domain:9000/")
    expect(config_entry.data[CONF_VERIFY_SSL]).to_be(True)
    expect(len(setup_entry.mock_calls)).to_equal(1)
