"""Test the fyta config flow."""

from unittest.mock import AsyncMock

from fyta_cli.fyta_exceptions import (
    FytaAuthentificationError,
    FytaConnectionError,
    FytaPasswordError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.fyta.const import CONF_EXPIRATION, DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.components.fyta._fixtures import mock_fyta_connector, mock_setup_entry
from tests.components.fyta.const import ACCESS_TOKEN, EXPIRATION, PASSWORD, USERNAME
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> None:
    """Trigger the hook executor path."""
    return None


async def _user_step(
    hass: HomeAssistant, flow_id: str, mock_setup_entry: AsyncMock
) -> None:
    """Test user step (helper function)."""
    result = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USERNAME)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            CONF_ACCESS_TOKEN: ACCESS_TOKEN,
            CONF_EXPIRATION: EXPIRATION,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    await _user_step(hass, result["flow_id"], mock_setup_entry)


@test.cases(
    test.case("connection", exception=FytaConnectionError, error={"base": "cannot_connect"}),
    test.case("auth", exception=FytaAuthentificationError, error={"base": "invalid_auth"}),
    test.case(
        "password",
        exception=FytaPasswordError,
        error={"base": "invalid_auth", CONF_PASSWORD: "password_error"},
    ),
    test.case("generic", exception=Exception, error={"base": "unknown"}),
)
async def form_exceptions(
    exception: type[Exception],
    error: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can handle Form exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_fyta_connector.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal(error)

    mock_fyta_connector.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USERNAME)
    expect(result["data"][CONF_USERNAME]).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)
    expect(result["data"][CONF_ACCESS_TOKEN]).to_equal(ACCESS_TOKEN)
    expect(result["data"][CONF_EXPIRATION]).to_equal(EXPIRATION)

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
) -> None:
    """Test duplicate setup handling."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=USERNAME,
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("connection", exception=FytaConnectionError, error={"base": "cannot_connect"}),
    test.case("auth", exception=FytaAuthentificationError, error={"base": "invalid_auth"}),
    test.case(
        "password",
        exception=FytaPasswordError,
        error={"base": "invalid_auth", CONF_PASSWORD: "password_error"},
    ),
    test.case("generic", exception=Exception, error={"base": "unknown"}),
)
async def reauth(
    exception: type[Exception],
    error: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth-flow works."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            CONF_ACCESS_TOKEN: ACCESS_TOKEN,
            CONF_EXPIRATION: EXPIRATION,
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_fyta_connector.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal(error)

    mock_fyta_connector.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "other_username", CONF_PASSWORD: "other_password"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_USERNAME]).to_equal("other_username")
    expect(entry.data[CONF_PASSWORD]).to_equal("other_password")
    expect(entry.data[CONF_ACCESS_TOKEN]).to_equal(ACCESS_TOKEN)
    expect(entry.data[CONF_EXPIRATION]).to_equal(EXPIRATION)


@test
async def dhcp_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_fyta_connector: AsyncMock = Depends(mock_fyta_connector),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test DHCP discovery flow."""
    service_info = DhcpServiceInfo(
        hostname="FYTA HUB",
        ip="1.2.3.4",
        macaddress="aabbccddeeff",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=service_info,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    await _user_step(hass, result["flow_id"], mock_setup_entry)
