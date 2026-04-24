"""Test the Pterodactyl config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pydactyl.exceptions import BadRequestError, PterodactylApiError
from requests.exceptions import HTTPError
from requests.models import Response
from tryke import Depends, expect, fixture, test

from homeassistant.components.pterodactyl.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_pterodactyl as mock_pterodactyl_fx,
    mock_setup_entry as mock_setup_entry_fx,
)
from .const import TEST_API_KEY, TEST_URL, TEST_USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


def mock_response() -> Response:
    """Mock HTTP response."""
    mock = Response()
    mock.status_code = 401
    return mock


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network and mock_setup_entry for every test."""


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_pterodactyl: AsyncMock = Depends(mock_pterodactyl_fx),
) -> None:
    """Test full flow without errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"],
        user_input=TEST_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_URL)
    expect(result["data"]).to_equal(TEST_USER_INPUT)


@test.cases(
    test.case(
        "pterodactyl_api_error",
        exception_type=PterodactylApiError,
        expected_error="cannot_connect",
    ),
    test.case(
        "bad_request_error",
        exception_type=BadRequestError,
        expected_error="cannot_connect",
    ),
    test.case(
        "generic_exception", exception_type=Exception, expected_error="unknown"
    ),
    test.case(
        "http_error_401",
        exception_type=HTTPError(response=mock_response()),
        expected_error="invalid_auth",
    ),
)
async def recovery_after_error(
    exception_type: type[Exception] | Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pterodactyl: AsyncMock = Depends(mock_pterodactyl_fx),
) -> None:
    """Test recovery after an error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_pterodactyl.client.servers.list_servers.side_effect = exception_type

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"],
        user_input=TEST_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_pterodactyl.reset_mock(side_effect=True)

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input=TEST_USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_URL)
    expect(result["data"]).to_equal(TEST_USER_INPUT)


@test
async def service_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _mock_pterodactyl: AsyncMock = Depends(mock_pterodactyl_fx),
) -> None:
    """Test config flow abort if the Pterodactyl server is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _mock_pterodactyl: AsyncMock = Depends(mock_pterodactyl_fx),
) -> None:
    """Test reauth config flow success."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: TEST_API_KEY}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_URL]).to_equal(TEST_URL)
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal(TEST_API_KEY)


@test.cases(
    test.case(
        "pterodactyl_api_error",
        exception_type=PterodactylApiError,
        expected_error="cannot_connect",
    ),
    test.case(
        "bad_request_error",
        exception_type=BadRequestError,
        expected_error="cannot_connect",
    ),
    test.case(
        "generic_exception", exception_type=Exception, expected_error="unknown"
    ),
    test.case(
        "http_error_401",
        exception_type=HTTPError(response=mock_response()),
        expected_error="invalid_auth",
    ),
)
async def reauth_recovery_after_error(
    exception_type: type[Exception] | Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_pterodactyl: AsyncMock = Depends(mock_pterodactyl_fx),
) -> None:
    """Test recovery after an error during re-authentication."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_pterodactyl.client.servers.list_servers.side_effect = exception_type

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: TEST_API_KEY}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_pterodactyl.reset_mock(side_effect=True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: TEST_API_KEY}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_URL]).to_equal(TEST_URL)
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal(TEST_API_KEY)
