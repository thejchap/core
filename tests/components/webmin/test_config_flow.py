"""Test the Webmin config flow."""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import AsyncMock, patch
from xmlrpc.client import Fault

from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.webmin.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import TEST_USER_INPUT, mock_setup_entry

from tests.common import async_load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _start_user_flow(hass: HomeAssistant) -> str:
    """Return a user-initiated flow after filling in host info."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    return result["flow_id"]


@test.cases(
    test.case("without_mac", fixture_name="webmin_update_without_mac.json"),
    test.case("with_mac", fixture_name="webmin_update.json"),
)
async def form_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    fixture_name: str,
) -> None:
    """Test a successful user initiated flow."""
    flow_id = await _start_user_flow(hass)
    with patch(
        "homeassistant.components.webmin.helpers.WebminInstance.update",
        return_value=await async_load_json_object_fixture(hass, fixture_name, DOMAIN),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id, TEST_USER_INPUT
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_USER_INPUT[CONF_HOST])
    expect(result["options"]).to_equal(TEST_USER_INPUT)

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "unauthorized",
        exception=ClientResponseError(
            request_info=None, history=None, status=HTTPStatus.UNAUTHORIZED
        ),
        error_type="invalid_auth",
    ),
    test.case(
        "bad_request",
        exception=ClientResponseError(
            request_info=None, history=None, status=HTTPStatus.BAD_REQUEST
        ),
        error_type="cannot_connect",
    ),
    test.case(
        "client_connection",
        exception=ClientConnectionError(),
        error_type="cannot_connect",
    ),
    test.case("unknown", exception=Exception(), error_type="unknown"),
    test.case(
        "fault",
        exception=Fault("5", "Webmin module net does not exist"),
        error_type="unknown",
    ),
)
async def form_user_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exception: Exception,
    error_type: str,
) -> None:
    """Test we handle errors."""
    flow_id = await _start_user_flow(hass)
    with patch(
        "homeassistant.components.webmin.helpers.WebminInstance.update",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id, TEST_USER_INPUT
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error_type})

    with patch(
        "homeassistant.components.webmin.helpers.WebminInstance.update",
        return_value=await async_load_json_object_fixture(
            hass, "webmin_update.json", DOMAIN
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_USER_INPUT
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_USER_INPUT[CONF_HOST])
    expect(result["options"]).to_equal(TEST_USER_INPUT)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a duplicate entry is rejected."""
    flow_id = await _start_user_flow(hass)
    with patch(
        "homeassistant.components.webmin.helpers.WebminInstance.update",
        return_value=await async_load_json_object_fixture(
            hass, "webmin_update.json", DOMAIN
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id, TEST_USER_INPUT
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_USER_INPUT[CONF_HOST])
    expect(result["options"]).to_equal(TEST_USER_INPUT)

    with patch(
        "homeassistant.components.webmin.helpers.WebminInstance.update",
        return_value=await async_load_json_object_fixture(
            hass, "webmin_update.json", DOMAIN
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_USER_INPUT
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
