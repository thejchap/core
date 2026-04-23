"""Test the MELCloud config flow."""

from http import HTTPStatus
from unittest.mock import MagicMock, patch

from aiohttp import ClientError, ClientResponseError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.melcloud.const import DOMAIN
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_async_zeroconf,
    mock_get_devices,
    mock_login,
    mock_request_info,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(mock_async_zeroconf),
    _ml: MagicMock = Depends(mock_login),
    _md: MagicMock = Depends(mock_get_devices),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    _login: MagicMock = Depends(mock_login),
    _devices: MagicMock = Depends(mock_get_devices),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.melcloud.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-email@test-domain.com", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("test-email@test-domain.com")
    expect(result2["data"]).to_equal(
        {
            "username": "test-email@test-domain.com",
            "token": "test-token",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("client_error", ClientError(), "cannot_connect"),
    test.case("timeout_error", TimeoutError(), "cannot_connect"),
    test.case("attribute_error", AttributeError(), "invalid_auth"),
)
async def form_errors(
    error: Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    login: MagicMock = Depends(mock_login),
    _devices: MagicMock = Depends(mock_get_devices),
) -> None:
    """Test we handle cannot connect error."""
    login.side_effect = error

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"username": "test-email@test-domain.com", "password": "test-password"},
    )

    expect(len(login.mock_calls)).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test.cases(
    test.case("unauthorized", HTTPStatus.UNAUTHORIZED, "invalid_auth"),
    test.case("forbidden", HTTPStatus.FORBIDDEN, "invalid_auth"),
    test.case("internal_server_error", HTTPStatus.INTERNAL_SERVER_ERROR, "cannot_connect"),
)
async def form_response_errors(
    error: HTTPStatus,
    message: str,
    hass: HomeAssistant = Depends(hass_fixture),
    login: MagicMock = Depends(mock_login),
    _devices: MagicMock = Depends(mock_get_devices),
    request_info: MagicMock = Depends(mock_request_info),
) -> None:
    """Test we handle response errors."""
    login.side_effect = ClientResponseError(request_info(), (), status=error)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"username": "test-email@test-domain.com", "password": "test-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(message)


@test
async def token_refresh(
    hass: HomeAssistant = Depends(hass_fixture),
    _login: MagicMock = Depends(mock_login),
    _devices: MagicMock = Depends(mock_get_devices),
) -> None:
    """Re-configuration with existing username should refresh token."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-email@test-domain.com", "token": "test-original-token"},
        unique_id="test-email@test-domain.com",
    )
    mock_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.melcloud.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                "username": "test-email@test-domain.com",
                "password": "test-password",
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    await hass.async_block_till_done()
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)

    entry = entries[0]
    expect(entry.data["username"]).to_equal("test-email@test-domain.com")
    expect(entry.data["token"]).to_equal("test-token")


@test
async def token_reauthentication(
    hass: HomeAssistant = Depends(hass_fixture),
    _login: MagicMock = Depends(mock_login),
    _devices: MagicMock = Depends(mock_get_devices),
) -> None:
    """Re-configuration with existing username should refresh token, if made invalid."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-email@test-domain.com", "token": "test-original-token"},
        unique_id="test-email@test-domain.com",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-email@test-domain.com", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("timeout_error", TimeoutError(), "cannot_connect"),
    test.case("attribute_error_get", AttributeError(name="get"), "invalid_auth"),
)
async def form_errors_reauthentication(
    error: Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    login: MagicMock = Depends(mock_login),
) -> None:
    """Test we handle cannot connect error."""
    login.side_effect = error
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-email@test-domain.com", "token": "test-original-token"},
        unique_id="test-email@test-domain.com",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-email@test-domain.com", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(reason)

    login.side_effect = None
    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-email@test-domain.com", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test.cases(
    test.case("unauthorized", HTTPStatus.UNAUTHORIZED, "invalid_auth"),
    test.case("forbidden", HTTPStatus.FORBIDDEN, "invalid_auth"),
    test.case("internal_server_error", HTTPStatus.INTERNAL_SERVER_ERROR, "cannot_connect"),
)
async def client_errors_reauthentication(
    error: HTTPStatus,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    login: MagicMock = Depends(mock_login),
    request_info: MagicMock = Depends(mock_request_info),
) -> None:
    """Test we handle cannot connect error."""
    login.side_effect = ClientResponseError(request_info(), (), status=error)
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-email@test-domain.com", "token": "test-original-token"},
        unique_id="test-email@test-domain.com",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-email@test-domain.com", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result["errors"]["base"]).to_equal(reason)
    expect(result["type"]).to_be(FlowResultType.FORM)

    login.side_effect = None
    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-email@test-domain.com", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test.cases(
    test.case("unauthorized", HTTPStatus.UNAUTHORIZED, "invalid_auth"),
    test.case("forbidden", HTTPStatus.FORBIDDEN, "invalid_auth"),
    test.case("internal_server_error", HTTPStatus.INTERNAL_SERVER_ERROR, "cannot_connect"),
)
async def reconfigure_flow(
    error: HTTPStatus,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    login: MagicMock = Depends(mock_login),
    request_info: MagicMock = Depends(mock_request_info),
) -> None:
    """Test re-configuration flow."""
    login.side_effect = ClientResponseError(request_info(), (), status=error)
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-email@test-domain.com", "token": "test-original-token"},
        unique_id="test-email@test-domain.com",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    expect(result["errors"]["base"]).to_equal(reason)
    expect(result["type"]).to_be(FlowResultType.FORM)

    login.side_effect = None
    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    entry = hass.config_entries.async_get_entry(mock_entry.entry_id)
    expect(entry).not_.to_be(None)
    expect(entry.title).to_equal("Mock Title")
    expect(entry.data).to_equal(
        {
            "username": "test-email@test-domain.com",
            "token": "test-token",
            "password": "test-password",
        }
    )


@test.cases(
    test.case("timeout_error", TimeoutError(), "cannot_connect"),
    test.case("attribute_error_get", AttributeError(name="get"), "invalid_auth"),
)
async def form_errors_reconfigure(
    error: Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    login: MagicMock = Depends(mock_login),
) -> None:
    """Test we handle cannot connect error."""
    login.side_effect = error
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-email@test-domain.com", "token": "test-original-token"},
        unique_id="test-email@test-domain.com",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reconfigure_flow(hass)

    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(reason)

    login.side_effect = None
    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    entry = hass.config_entries.async_get_entry(mock_entry.entry_id)
    expect(entry).not_.to_be(None)
    expect(entry.title).to_equal("Mock Title")
    expect(entry.data).to_equal(
        {
            "username": "test-email@test-domain.com",
            "token": "test-token",
            "password": "test-password",
        }
    )
