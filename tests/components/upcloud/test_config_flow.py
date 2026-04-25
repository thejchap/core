"""Tests for the UpCloud config flow."""

from unittest.mock import patch

import requests.exceptions
import requests_mock as rm
from requests_mock import ANY
from tryke import Depends, expect, fixture, test
from upcloud_api import UpCloudAPIError

from homeassistant import config_entries
from homeassistant.components.upcloud.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import requests_mock_mocker

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

FIXTURE_USER_INPUT = {
    CONF_USERNAME: "user",
    CONF_PASSWORD: "pass",
}

FIXTURE_USER_INPUT_OPTIONS = {
    CONF_SCAN_INTERVAL: "120",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_set_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the setup form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=None
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: rm.Mocker = Depends(requests_mock_mocker),
) -> None:
    """Test we show user form on connection error."""
    requests_mock.request(ANY, ANY, exc=requests.exceptions.ConnectionError())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=FIXTURE_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def login_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: rm.Mocker = Depends(requests_mock_mocker),
) -> None:
    """Test we show user form with appropriate error on response failure."""
    requests_mock.request(
        ANY,
        ANY,
        exc=UpCloudAPIError(
            error_code="AUTHENTICATION_FAILED",
            error_message="Authentication failed using the given username and password.",
        ),
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=FIXTURE_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: rm.Mocker = Depends(requests_mock_mocker),
) -> None:
    """Test successful flow provides entry creation data."""
    requests_mock.request(ANY, "/1.3/account", text='{"account":{"username":"user"}}')
    requests_mock.request(ANY, "/1.3/server", text='{"servers": {"server":[]}}')
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=FIXTURE_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_USERNAME]).to_equal(FIXTURE_USER_INPUT[CONF_USERNAME])
    expect(result["data"][CONF_PASSWORD]).to_equal(FIXTURE_USER_INPUT[CONF_PASSWORD])


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options produce expected data."""

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=FIXTURE_USER_INPUT, options=FIXTURE_USER_INPUT_OPTIONS
    )
    config_entry.add_to_hass(hass)

    with patch("homeassistant.components.upcloud.async_setup_entry", return_value=True):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=FIXTURE_USER_INPUT_OPTIONS,
    )
    expect(result["data"][CONF_SCAN_INTERVAL]).to_equal(
        int(FIXTURE_USER_INPUT_OPTIONS[CONF_SCAN_INTERVAL])
    )


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    requests_mock: rm.Mocker = Depends(requests_mock_mocker),
) -> None:
    """Test duplicate entry aborts and updates data."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_USER_INPUT[CONF_USERNAME],
        data=FIXTURE_USER_INPUT,
        options=FIXTURE_USER_INPUT_OPTIONS,
    )
    config_entry.add_to_hass(hass)

    new_user_input = FIXTURE_USER_INPUT.copy()
    new_user_input[CONF_PASSWORD] += "_changed"

    requests_mock.request(ANY, "/1.3/account", text='{"account":{"username":"user"}}')
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=new_user_input
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_USERNAME]).to_equal(new_user_input[CONF_USERNAME])
    expect(config_entry.data[CONF_PASSWORD]).to_equal(new_user_input[CONF_PASSWORD])
