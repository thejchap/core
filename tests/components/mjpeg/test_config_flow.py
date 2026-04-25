"""Tests for the MJPEG IP Camera config flow."""

from unittest.mock import AsyncMock

import requests
from requests_mock import Mocker
from tryke import Depends, expect, fixture, test

from homeassistant.components.mjpeg.const import (
    CONF_MJPEG_URL,
    CONF_STILL_IMAGE_URL,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_mjpeg_requests, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mjpeg_requests: Mocker = Depends(mock_mjpeg_requests),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Spy cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
            CONF_USERNAME: "frenck",
            CONF_PASSWORD: "omgpuppies",
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Spy cam")
    expect(dict(result2.get("data"))).to_equal({})
    expect(dict(result2.get("options"))).to_equal(
        {
            CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_PASSWORD: "omgpuppies",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
            CONF_USERNAME: "frenck",
            CONF_VERIFY_SSL: False,
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(mjpeg_requests.call_count).to_equal(2)


@test
async def full_flow_with_authentication_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mjpeg_requests: Mocker = Depends(mock_mjpeg_requests),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow with invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    mjpeg_requests.get(
        "https://example.com/mjpeg", text="Access Denied!", status_code=401
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Sky cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_PASSWORD: "omgpuppies",
            CONF_USERNAME: "frenck",
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("user")
    expect(result2.get("errors")).to_equal({"username": "invalid_auth"})

    expect(len(setup_entry.mock_calls)).to_equal(0)
    expect(mjpeg_requests.call_count).to_equal(2)

    mjpeg_requests.get("https://example.com/mjpeg", text="resp")
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_NAME: "Sky cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_PASSWORD: "supersecret",
            CONF_USERNAME: "frenck",
        },
    )

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3.get("title")).to_equal("Sky cam")
    expect(dict(result3.get("data"))).to_equal({})
    expect(dict(result3.get("options"))).to_equal(
        {
            CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_PASSWORD: "supersecret",
            CONF_STILL_IMAGE_URL: None,
            CONF_USERNAME: "frenck",
            CONF_VERIFY_SSL: True,
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(mjpeg_requests.call_count).to_equal(3)


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mjpeg_requests: Mocker = Depends(mock_mjpeg_requests),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    mjpeg_requests.get(
        "https://example.com/mjpeg", exc=requests.exceptions.ConnectionError
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "My cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("user")
    expect(result2.get("errors")).to_equal({"mjpeg_url": "cannot_connect"})

    expect(len(setup_entry.mock_calls)).to_equal(0)
    expect(mjpeg_requests.call_count).to_equal(1)

    mjpeg_requests.get("https://example.com/mjpeg", text="resp")

    mjpeg_requests.get(
        "https://example.com/still", exc=requests.exceptions.ConnectionError
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_NAME: "My cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
        },
    )

    expect(result3.get("type")).to_be(FlowResultType.FORM)
    expect(result3.get("step_id")).to_equal("user")
    expect(result3.get("errors")).to_equal({"still_image_url": "cannot_connect"})

    expect(len(setup_entry.mock_calls)).to_equal(0)
    expect(mjpeg_requests.call_count).to_equal(3)

    mjpeg_requests.get("https://example.com/still", text="resp")

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        user_input={
            CONF_NAME: "My cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
        },
    )

    expect(result4.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result4.get("title")).to_equal("My cam")
    expect(dict(result4.get("data"))).to_equal({})
    expect(dict(result4.get("options"))).to_equal(
        {
            CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_PASSWORD: "",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
            CONF_USERNAME: None,
            CONF_VERIFY_SSL: True,
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(mjpeg_requests.call_count).to_equal(5)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mjpeg: Mocker = Depends(mock_mjpeg_requests),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we abort if the MJPEG IP Camera is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "My cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("already_configured")


@test.skip("options flow uses init_integration which sets up component fully")
async def options_flow() -> None:
    """Test options config flow."""
