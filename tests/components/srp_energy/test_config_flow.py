"""Test the SRP Energy config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.srp_energy.const import CONF_IS_TOU, DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import (
    CONF_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SOURCE,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    ACCNT_ID,
    ACCNT_ID_2,
    ACCNT_IS_TOU,
    ACCNT_NAME,
    ACCNT_NAME_2,
    ACCNT_PASSWORD,
    ACCNT_USERNAME,
    TEST_CONFIG_CABIN,
    TEST_CONFIG_HOME,
)
from ._fixtures import (
    init_integration,
    mock_setup_entry,
    mock_srp_energy_config_flow,
    setup_hass_config,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _cfg: None = Depends(setup_hass_config),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _srp: MagicMock = Depends(mock_srp_energy_config_flow),
) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.srp_energy.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"], user_input=TEST_CONFIG_HOME
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(ACCNT_NAME)

        expect("data" in result).to_be(True)
        expect(result["data"][CONF_ID]).to_equal(ACCNT_ID)
        expect(result["data"][CONF_USERNAME]).to_equal(ACCNT_USERNAME)
        expect(result["data"][CONF_PASSWORD]).to_equal(ACCNT_PASSWORD)
        expect(result["data"][CONF_IS_TOU]).to_equal(ACCNT_IS_TOU)
        expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def form_invalid_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_srp: MagicMock = Depends(mock_srp_energy_config_flow),
) -> None:
    """Test flow to handle invalid account error."""
    mock_srp.validate.side_effect = ValueError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input=TEST_CONFIG_HOME
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_account"})


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_srp: MagicMock = Depends(mock_srp_energy_config_flow),
) -> None:
    """Test flow to handle invalid authentication error."""
    mock_srp.validate.return_value = False

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input=TEST_CONFIG_HOME
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_srp: MagicMock = Depends(mock_srp_energy_config_flow),
) -> None:
    """Test flow to handle invalid authentication error."""
    mock_srp.validate.side_effect = Exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input=TEST_CONFIG_HOME
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def flow_entry_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test user input for config_entry that already exists."""
    expect(integration.state).to_be(ConfigEntryState.LOADED)
    expect(integration.data[CONF_ID]).to_equal(ACCNT_ID)
    expect(integration.unique_id).to_equal(ACCNT_ID)

    user_input_second = TEST_CONFIG_HOME
    user_input_second[CONF_ID] = integration.data[CONF_ID]

    expect(user_input_second[CONF_ID]).to_equal(ACCNT_ID)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=user_input_second
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_multiple_configs(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test multiple config entries."""
    expect(integration.state).to_be(ConfigEntryState.LOADED)
    expect(integration.data[CONF_ID]).to_equal(ACCNT_ID)
    expect(integration.unique_id).to_equal(ACCNT_ID)

    expect(TEST_CONFIG_CABIN[CONF_ID] != ACCNT_ID).to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=TEST_CONFIG_CABIN
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(ACCNT_NAME_2)

    expect("data" in result).to_be(True)
    expect(result["data"][CONF_ID]).to_equal(ACCNT_ID_2)
    expect(result["data"][CONF_USERNAME]).to_equal(ACCNT_USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(ACCNT_PASSWORD)
    expect(result["data"][CONF_IS_TOU]).to_equal(ACCNT_IS_TOU)

    entries = hass.config_entries.async_entries()
    domain_entries = [entry for entry in entries if entry.domain == DOMAIN]
    expect(len(domain_entries)).to_equal(2)


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test reconfiguring an existing entry."""
    result = await integration.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ID: ACCNT_ID,
            CONF_NAME: ACCNT_NAME + "reconf",
            CONF_USERNAME: ACCNT_USERNAME + "reconf",
            CONF_PASSWORD: ACCNT_PASSWORD + "reconf",
            CONF_IS_TOU: not ACCNT_IS_TOU,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(integration.data).to_equal(
        {
            CONF_ID: ACCNT_ID,
            CONF_NAME: ACCNT_NAME + "reconf",
            CONF_USERNAME: ACCNT_USERNAME + "reconf",
            CONF_PASSWORD: ACCNT_PASSWORD + "reconf",
            CONF_IS_TOU: not ACCNT_IS_TOU,
        }
    )


@test
async def reconfigure_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    integration: MockConfigEntry = Depends(init_integration),
    mock_srp: MagicMock = Depends(mock_srp_energy_config_flow),
    _setup: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfiguring an existing entry."""
    result = await integration.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_srp.validate.side_effect = ValueError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ID: ACCNT_ID,
            CONF_NAME: ACCNT_NAME + "reconf",
            CONF_USERNAME: ACCNT_USERNAME + "reconf",
            CONF_PASSWORD: ACCNT_PASSWORD + "reconf",
            CONF_IS_TOU: not ACCNT_IS_TOU,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_account"})

    mock_srp.validate.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ID: ACCNT_ID,
            CONF_NAME: ACCNT_NAME + "reconf",
            CONF_USERNAME: ACCNT_USERNAME + "reconf",
            CONF_PASSWORD: ACCNT_PASSWORD + "reconf",
            CONF_IS_TOU: not ACCNT_IS_TOU,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def reconfigure_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    integration: MockConfigEntry = Depends(init_integration),
    mock_srp: MagicMock = Depends(mock_srp_energy_config_flow),
    _setup: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfiguring an existing entry and handling unknown error."""
    result = await integration.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_srp.validate.side_effect = Exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ID: ACCNT_ID,
            CONF_NAME: ACCNT_NAME + "reconf",
            CONF_USERNAME: ACCNT_USERNAME + "reconf",
            CONF_PASSWORD: ACCNT_PASSWORD + "reconf",
            CONF_IS_TOU: not ACCNT_IS_TOU,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")
