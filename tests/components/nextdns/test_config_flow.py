"""Define tests for the NextDNS config flow."""

from unittest.mock import AsyncMock

from nextdns import ApiError, InvalidApiKeyError, ProfileInfo
from tenacity import RetryError
from tryke import Depends, expect, fixture, test

from homeassistant.components.nextdns.const import CONF_PROFILE_ID, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_PROFILE_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import init_integration
from ._fixtures import (
    mock_config_entry,
    mock_nextdns,
    mock_nextdns_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def form_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_nextdns_client),
    nextdns: AsyncMock = Depends(mock_nextdns),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "fake_api_key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("profiles")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROFILE_NAME: "Fake Profile"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Fake Profile")
    expect(result["data"][CONF_API_KEY]).to_equal("fake_api_key")
    expect(result["data"][CONF_PROFILE_ID]).to_equal("xyz12")
    expect(result["result"].unique_id).to_equal("xyz12")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("api_error", exc=ApiError("API Error"), base_error="cannot_connect"),
    test.case("invalid_key", exc=InvalidApiKeyError(), base_error="invalid_api_key"),
    test.case("retry_error", exc=RetryError("Retry Error"), base_error="cannot_connect"),
    test.case("timeout", exc=TimeoutError(), base_error="cannot_connect"),
    test.case("value_error", exc=ValueError(), base_error="unknown"),
)
async def form_errors(
    exc: Exception,
    base_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_nextdns_client),
    nextdns: AsyncMock = Depends(mock_nextdns),
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    nextdns.create.side_effect = exc

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "fake_api_key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": base_error})

    nextdns.create.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "fake_api_key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("profiles")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROFILE_NAME: "Fake Profile"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Fake Profile")
    expect(result["data"][CONF_API_KEY]).to_equal("fake_api_key")
    expect(result["data"][CONF_PROFILE_ID]).to_equal("xyz12")
    expect(result["result"].unique_id).to_equal("xyz12")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_nextdns_client),
    nextdns: AsyncMock = Depends(mock_nextdns),
) -> None:
    """Test that errors are shown when duplicates are added."""
    await init_integration(hass, entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "fake_api_key"},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROFILE_NAME: "Fake Profile"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_nextdns_client),
    nextdns: AsyncMock = Depends(mock_nextdns),
) -> None:
    """Test starting a reauthentication flow."""
    await init_integration(hass, entry)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_API_KEY]).to_equal("new_api_key")


@test
async def reauth_no_profile(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_nextdns_client),
) -> None:
    """Test reauthentication flow when the profile is no longer available."""
    await init_integration(hass, entry)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    client.profiles = [
        ProfileInfo(id="abcd098", fingerprint="abcd098", name="New Profile")
    ]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("profile_not_available")


@test.cases(
    test.case("api_error", exc=ApiError("API Error"), base_error="cannot_connect"),
    test.case("invalid_key", exc=InvalidApiKeyError(), base_error="invalid_api_key"),
    test.case("retry_error", exc=RetryError("Retry Error"), base_error="cannot_connect"),
    test.case("timeout", exc=TimeoutError(), base_error="cannot_connect"),
    test.case("value_error", exc=ValueError(), base_error="unknown"),
)
async def reauth_errors(
    exc: Exception,
    base_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_nextdns_client),
    nextdns: AsyncMock = Depends(mock_nextdns),
) -> None:
    """Test reauthentication flow with errors."""
    await init_integration(hass, entry)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    nextdns.create.side_effect = exc

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["errors"]).to_equal({"base": base_error})

    nextdns.create.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_API_KEY]).to_equal("new_api_key")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_nextdns_client),
) -> None:
    """Test starting a reconfigure flow."""
    await init_integration(hass, entry)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_API_KEY]).to_equal("new_api_key")


@test.cases(
    test.case("api_error", exc=ApiError("API Error"), base_error="cannot_connect"),
    test.case("invalid_key", exc=InvalidApiKeyError(), base_error="invalid_api_key"),
    test.case("retry_error", exc=RetryError("Retry Error"), base_error="cannot_connect"),
    test.case("timeout", exc=TimeoutError(), base_error="cannot_connect"),
    test.case("value_error", exc=ValueError(), base_error="unknown"),
)
async def reconfiguration_errors(
    exc: Exception,
    base_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_nextdns_client),
    nextdns: AsyncMock = Depends(mock_nextdns),
) -> None:
    """Test reconfigure flow with errors."""
    await init_integration(hass, entry)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    nextdns.create.side_effect = exc

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["errors"]).to_equal({"base": base_error})

    nextdns.create.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_API_KEY]).to_equal("new_api_key")


@test
async def reconfigure_flow_no_profile(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_nextdns_client),
) -> None:
    """Test reconfigure flow when the profile is no longer available."""
    await init_integration(hass, entry)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    client.profiles = [
        ProfileInfo(id="abcd098", fingerprint="abcd098", name="New Profile")
    ]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new_api_key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("profile_not_available")
