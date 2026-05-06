"""Test the Control4 config flow."""

from unittest.mock import AsyncMock, MagicMock

from aiohttp.client_exceptions import ClientError
from pyControl4.error_handling import BadCredentials, NotFound, Unauthorized
from tryke import Depends, expect, fixture, test

from homeassistant.components.control4.const import DEFAULT_SCAN_INTERVAL, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    MOCK_HOST,
    MOCK_PASSWORD,
    MOCK_USERNAME,
    mock_c4_account,
    mock_c4_director,
    mock_config_entry,
    mock_patch_platforms,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _platforms: None = Depends(mock_patch_platforms),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    c4_account: MagicMock = Depends(mock_c4_account),
    c4_director: MagicMock = Depends(mock_c4_director),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full config flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("control4_model_00AA00AA00AA")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
            "controller_unique_id": "control4_model_00AA00AA00AA",
        }
    )
    expect(result["result"].unique_id).to_equal("00:aa:00:aa:00:aa")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "bad_credentials",
        exception=BadCredentials("Invalid username or password"),
        error="invalid_auth",
    ),
    test.case(
        "unauthorized",
        exception=Unauthorized("Permission denied"),
        error="invalid_auth",
    ),
    test.case(
        "not_found",
        exception=NotFound("something"),
        error="controller_not_found",
    ),
    test.case(
        "unknown",
        exception=Exception("Some other exception"),
        error="unknown",
    ),
)
async def user_flow_errors(
    *,
    exception: Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    c4_account: MagicMock = Depends(mock_c4_account),
    c4_director: MagicMock = Depends(mock_c4_director),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle errors in the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    c4_account.getAccountBearerToken.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    c4_account.getAccountBearerToken.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case(
        "unauthorized",
        exception=Unauthorized("Permission denied"),
        error="director_auth_failed",
    ),
    test.case(
        "client_error",
        exception=ClientError,
        error="cannot_connect",
    ),
    test.case(
        "timeout",
        exception=TimeoutError,
        error="cannot_connect",
    ),
    test.case(
        "unknown",
        exception=Exception("Some other exception"),
        error="unknown",
    ),
)
async def user_flow_director_errors(
    *,
    exception: Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    c4_account: MagicMock = Depends(mock_c4_account),
    c4_director: MagicMock = Depends(mock_c4_director),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle director auth failure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    c4_director.getAllItemInfo.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    c4_director.getAllItemInfo.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    c4_account: MagicMock = Depends(mock_c4_account),
    c4_director: MagicMock = Depends(mock_c4_director),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that duplicate entries are not created."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCK_HOST,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def option_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow options."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 4},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_SCAN_INTERVAL: 4})


@test
async def option_flow_defaults(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow options."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL})
