"""Test the NASweb config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test
from webio_api.api_client import AuthError

from homeassistant import config_entries
from homeassistant.components.nasweb.const import DOMAIN
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.network import NoURLAvailableError

from tests.components.nasweb._fixtures import (
    BASE_CONFIG_FLOW,
    BASE_COORDINATOR,
    BASE_NASWEB_DATA,
    TEST_SERIAL_NUMBER,
    mock_setup_entry,
    validate_input_all_ok,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_USER_INPUT = {
    CONF_HOST: "1.1.1.1",
    CONF_USERNAME: "test-username",
    CONF_PASSWORD: "test-password",
}


@fixture
def _trigger_executor(
    _mse: AsyncMock = Depends(mock_setup_entry),
    _net: None = Depends(mock_network),
) -> None:
    """Wire the module-scope fixtures."""


async def _add_test_config_entry(hass: HomeAssistant) -> ConfigFlowResult:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )
    await hass.async_block_till_done()
    return result2


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
    _validate: dict[str, AsyncMock | MagicMock] = Depends(validate_input_all_ok),
) -> None:
    """Test the form."""
    result = await _add_test_config_entry(hass)

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("1.1.1.1")
    expect(result.get("data")).to_equal(TEST_USER_INPUT)

    config_entry = result.get("result")
    expect(config_entry is not None).to_be(True)
    assert config_entry is not None
    expect(config_entry.unique_id).to_equal(TEST_SERIAL_NUMBER)
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    _validate: dict[str, AsyncMock | MagicMock] = Depends(validate_input_all_ok),
) -> None:
    """Test cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(BASE_CONFIG_FLOW + "WebioAPI.check_connection", return_value=False):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_USER_INPUT
        )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "cannot_connect"})


@test
async def form_invalid_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    _validate: dict[str, AsyncMock | MagicMock] = Depends(validate_input_all_ok),
) -> None:
    """Test invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        BASE_CONFIG_FLOW + "WebioAPI.refresh_device_info",
        side_effect=AuthError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_USER_INPUT
        )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "invalid_auth"})


@test
async def form_missing_internal_url(
    hass: HomeAssistant = Depends(hass_fixture),
    _validate: dict[str, AsyncMock | MagicMock] = Depends(validate_input_all_ok),
) -> None:
    """Test missing internal url."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        BASE_NASWEB_DATA + "NASwebData.get_webhook_url",
        side_effect=NoURLAvailableError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_USER_INPUT
        )
        expect(result2.get("type")).to_be(FlowResultType.FORM)
        expect(result2.get("errors")).to_equal({"base": "missing_internal_url"})


@test
async def form_missing_nasweb_data(
    hass: HomeAssistant = Depends(hass_fixture),
    _validate: dict[str, AsyncMock | MagicMock] = Depends(validate_input_all_ok),
) -> None:
    """Test missing nasweb data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        BASE_CONFIG_FLOW + "WebioAPI.get_serial_number",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_USER_INPUT
        )
        expect(result2.get("type")).to_be(FlowResultType.FORM)
        expect(result2.get("errors")).to_equal({"base": "missing_nasweb_data"})
    with patch(BASE_CONFIG_FLOW + "WebioAPI.status_subscription", return_value=False):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_USER_INPUT
        )
        expect(result2.get("type")).to_be(FlowResultType.FORM)
        expect(result2.get("errors")).to_equal({"base": "missing_nasweb_data"})


@test
async def missing_status(
    hass: HomeAssistant = Depends(hass_fixture),
    _validate: dict[str, AsyncMock | MagicMock] = Depends(validate_input_all_ok),
) -> None:
    """Test missing status update."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        BASE_COORDINATOR + "NotificationCoordinator.check_connection",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_USER_INPUT
        )
        expect(result2.get("type")).to_be(FlowResultType.FORM)
        expect(result2.get("errors")).to_equal({"base": "missing_status"})


@test
async def form_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    _validate: dict[str, AsyncMock | MagicMock] = Depends(validate_input_all_ok),
) -> None:
    """Test other exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nasweb.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], TEST_USER_INPUT
        )
        expect(result2.get("type")).to_be(FlowResultType.FORM)
        expect(result2.get("errors")).to_equal({"base": "unknown"})


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _validate: dict[str, AsyncMock | MagicMock] = Depends(validate_input_all_ok),
) -> None:
    """Test already configured device."""
    result = await _add_test_config_entry(hass)
    config_entry = result.get("result")
    expect(config_entry is not None).to_be(True)
    assert config_entry is not None
    expect(config_entry.unique_id).to_equal(TEST_SERIAL_NUMBER)

    result2_1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2_2 = await hass.config_entries.flow.async_configure(
        result2_1["flow_id"], TEST_USER_INPUT
    )
    await hass.async_block_till_done()

    expect(result2_2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2_2.get("reason")).to_equal("already_configured")
