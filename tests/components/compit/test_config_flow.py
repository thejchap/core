"""Test the Compit config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.compit.config_flow import CannotConnect, InvalidAuth
from homeassistant.components.compit.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_compit_api,
    mock_config_entry as mock_config_entry_fixture,
    mock_setup_entry,
)
from .consts import CONFIG_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def async_step_user_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_compit_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user step with successful authentication."""
    api.return_value = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)
    expect(result["description_placeholders"]).to_equal(
        {"compit_url": "https://inext.compit.pl/"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(CONFIG_INPUT[CONF_EMAIL])
    expect(result["data"]).to_equal(CONFIG_INPUT)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=InvalidAuth(), expected_error="invalid_auth"),
    test.case(
        "cannot_connect", exception=CannotConnect(), expected_error="cannot_connect"
    ),
    test.case("unknown_exception", exception=Exception(), expected_error="unknown"),
    test.case("false_value", exception=False, expected_error="unknown"),
)
async def async_step_user_failed_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_compit_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: object,
    expected_error: str,
) -> None:
    """Test user step with invalid authentication then success after error is cleared."""
    api.side_effect = [exception, True]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    # Test success after error is cleared.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_INPUT
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(CONFIG_INPUT[CONF_EMAIL])
    expect(result["data"]).to_equal(CONFIG_INPUT)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def async_step_reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    api: AsyncMock = Depends(mock_compit_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth step with successful authentication."""
    api.return_value = True

    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_EMAIL: CONFIG_INPUT[CONF_EMAIL],
            CONF_PASSWORD: "new-password",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=InvalidAuth(), expected_error="invalid_auth"),
    test.case(
        "cannot_connect", exception=CannotConnect(), expected_error="cannot_connect"
    ),
    test.case("unknown_exception", exception=Exception(), expected_error="unknown"),
)
async def async_step_reauth_confirm_failed_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    api: AsyncMock = Depends(mock_compit_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test reauth confirm step with invalid auth then success after error is cleared."""
    api.side_effect = [exception, True]

    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    # Test success after error is cleared.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: CONFIG_INPUT[CONF_EMAIL], CONF_PASSWORD: "correct-password"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_EMAIL: CONFIG_INPUT[CONF_EMAIL],
            CONF_PASSWORD: "correct-password",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)
