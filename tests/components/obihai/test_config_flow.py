"""Test the Obihai config flow."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.obihai.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import DHCP_SERVICE_INFO, USER_INPUT, MockPyObihai, get_schema_suggestion
from ._fixtures import mock_gaierror, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture

VALIDATE_AUTH_PATCH = "homeassistant.components.obihai.config_flow.validate_auth"


@fixture
def _trigger_executor(_setup: AsyncMock = Depends(mock_setup_entry)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the user initiated form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with (
        patch(VALIDATE_AUTH_PATCH, return_value=MockPyObihai()),
        patch("homeassistant.components.obihai.config_flow.gethostbyname"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.10.10.30")
    expect(result["data"]).to_equal({**USER_INPUT})

    expect(len(setup.mock_calls)).to_equal(1)


@test
async def auth_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the authentication error for user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(VALIDATE_AUTH_PATCH, return_value=False),
        patch("homeassistant.components.obihai.config_flow.gethostbyname"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("invalid_auth")


@test
async def connect_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _err: Generator = Depends(mock_gaierror),
) -> None:
    """Test we get the connection error for user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("cannot_connect")


@test
async def dhcp_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that DHCP discovery works."""
    with (
        patch(VALIDATE_AUTH_PATCH, return_value=MockPyObihai()),
        patch("homeassistant.components.obihai.config_flow.gethostbyname"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

        flows = hass.config_entries.flow.async_progress()
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(len(flows)).to_equal(1)
        expect(
            get_schema_suggestion(result["data_schema"].schema, CONF_USERNAME)
        ).to_equal(USER_INPUT[CONF_USERNAME])
        expect(
            get_schema_suggestion(result["data_schema"].schema, CONF_PASSWORD)
        ).to_equal(USER_INPUT[CONF_PASSWORD])
        expect(
            get_schema_suggestion(result["data_schema"].schema, CONF_HOST)
        ).to_equal(DHCP_SERVICE_INFO.ip)
        expect(flows[0].get("context", {}).get("source")).to_equal(
            config_entries.SOURCE_DHCP
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def dhcp_flow_auth_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that DHCP fails if creds aren't default."""
    with (
        patch(VALIDATE_AUTH_PATCH, return_value=False),
        patch("homeassistant.components.obihai.config_flow.gethostbyname"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

        expect(result["step_id"]).to_equal("dhcp_confirm")
        expect(
            get_schema_suggestion(result["data_schema"].schema, CONF_USERNAME)
        ).to_equal("")
        expect(
            get_schema_suggestion(result["data_schema"].schema, CONF_PASSWORD)
        ).to_equal("")
        expect(
            get_schema_suggestion(result["data_schema"].schema, CONF_HOST)
        ).to_equal(DHCP_SERVICE_INFO.ip)

    with patch("homeassistant.components.obihai.config_flow.gethostbyname"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: DHCP_SERVICE_INFO.ip,
                CONF_USERNAME: "",
                CONF_PASSWORD: "",
            },
        )

    expect(result["errors"]["base"]).to_equal("invalid_auth")
    expect(result["step_id"]).to_equal("user")
