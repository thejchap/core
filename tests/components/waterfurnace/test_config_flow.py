"""Test the WaterFurnace config flow."""

from unittest.mock import AsyncMock, Mock

from tryke import Depends, expect, fixture, test
from waterfurnace.waterfurnace import WFCredentialError, WFException

from homeassistant.components.waterfurnace.const import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_setup_entry, mock_waterfurnace_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("WaterFurnace test_user")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
        }
    )
    expect(result["result"].unique_id).to_equal("test_account_id")
    expect(client.login.called).to_be(True)


@test.cases(
    test.case(
        "invalid_auth",
        exception=WFCredentialError("Invalid credentials"),
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        exception=WFException("Connection failed"),
        error="cannot_connect",
    ),
    test.case(
        "unknown",
        exception=Exception("Unexpected error"),
        error="unknown",
    ),
)
async def user_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test user flow with errors and recovery."""
    client.login.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "bad_user", CONF_PASSWORD: "bad_password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow with no devices."""
    client.devices = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "bad_user", CONF_PASSWORD: "bad_password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_devices"})

    client.devices = [Mock(gwid="TEST_GWID_12345")]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_account_id_none(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow when account_id is None."""
    client.account_id = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: Mock = Depends(mock_waterfurnace_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user flow when device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def import_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: Mock = Depends(mock_waterfurnace_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful import flow from YAML."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("WaterFurnace test_user")
    expect(result["data"]).to_equal(
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"}
    )
    expect(result["result"].unique_id).to_equal("test_account_id")


@test
async def import_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: Mock = Depends(mock_waterfurnace_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test import flow when device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_auth",
        exception=WFCredentialError("Invalid credentials"),
        reason="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        exception=WFException("Connection failed"),
        reason="cannot_connect",
    ),
    test.case("unknown", exception=Exception("Unexpected error"), reason="unknown"),
)
async def import_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
    *,
    exception: Exception,
    reason: str,
) -> None:
    """Test import flow with connection error."""
    client.login.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def import_flow_account_id_none(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
) -> None:
    """Test import flow when account_id is None."""
    client.account_id = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def import_flow_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
) -> None:
    """Test import flow with no devices."""
    client.devices = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices")


@test
async def reauth_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: Mock = Depends(mock_waterfurnace_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful reauth flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "new_user", CONF_PASSWORD: "new_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.title).to_equal("WaterFurnace new_user")
    expect(config_entry.data[CONF_USERNAME]).to_equal("new_user")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_password")


@test.cases(
    test.case(
        "invalid_auth",
        exception=WFCredentialError("Invalid credentials"),
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        exception=WFException("Connection failed"),
        error="cannot_connect",
    ),
    test.case("unknown", exception=Exception("Unexpected error"), error="unknown"),
)
async def reauth_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test reauth flow with errors and recovery."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    client.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "bad_password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "new_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_flow_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth flow aborts when a different account is used."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    client.account_id = "different_account_id"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "other_user", CONF_PASSWORD: "other_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")


@test
async def reauth_flow_no_account_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(mock_waterfurnace_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth flow when no account ID is returned."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    client.account_id = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "new_password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
