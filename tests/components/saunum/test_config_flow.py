"""Test the Saunum config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pysaunum import SaunumConnectionError, SaunumException
from tryke import Depends, expect, fixture, test

from homeassistant.components.saunum.const import (
    DOMAIN,
    OPT_PRESET_NAME_TYPE_1,
    OPT_PRESET_NAME_TYPE_2,
    OPT_PRESET_NAME_TYPE_3,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_saunum_client,
    mock_saunum_client_class,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_USER_INPUT = {CONF_HOST: "192.168.1.100"}
TEST_RECONFIGURE_INPUT = {CONF_HOST: "192.168.1.200"}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Saunum")
    expect(result["data"]).to_equal(TEST_USER_INPUT)


@test.cases(
    test.case(
        "connection_error",
        side_effect=SaunumConnectionError("Connection failed"),
        error_base="cannot_connect",
    ),
    test.case(
        "saunum_exception",
        side_effect=SaunumException("Read error"),
        error_base="cannot_connect",
    ),
    test.case(
        "unknown",
        side_effect=Exception("Unexpected error"),
        error_base="unknown",
    ),
)
async def form_errors(
    side_effect: Exception,
    error_base: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: MagicMock = Depends(mock_saunum_client_class),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test error handling and recovery."""
    client_class.create.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    client_class.create.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Saunum")
    expect(result["data"]).to_equal(TEST_USER_INPUT)


@test
async def form_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate entry handling."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("reconfigure_input", user_input=TEST_RECONFIGURE_INPUT),
    test.case("user_input", user_input=TEST_USER_INPUT),
)
async def reconfigure_flow(
    user_input: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal(user_input)


@test.cases(
    test.case(
        "connection_error",
        side_effect=SaunumConnectionError("Connection failed"),
        error_base="cannot_connect",
    ),
    test.case(
        "saunum_exception",
        side_effect=SaunumException("Read error"),
        error_base="cannot_connect",
    ),
    test.case(
        "unknown",
        side_effect=Exception("Unexpected error"),
        error_base="unknown",
    ),
)
async def reconfigure_errors(
    side_effect: Exception,
    error_base: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client_class: MagicMock = Depends(mock_saunum_client_class),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow error handling."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    client_class.create.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_RECONFIGURE_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    client_class.create.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_RECONFIGURE_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal(TEST_RECONFIGURE_INPUT)


@test
async def reconfigure_to_existing_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow aborts when changing to a host used by another entry."""
    config_entry.add_to_hass(hass)

    second_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_RECONFIGURE_INPUT,
        title="Saunum 2",
    )
    second_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_RECONFIGURE_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry.data).to_equal(TEST_USER_INPUT)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test options flow for configuring preset names."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    custom_options = {
        OPT_PRESET_NAME_TYPE_1: "Finnish Sauna",
        OPT_PRESET_NAME_TYPE_2: "Turkish Bath",
        OPT_PRESET_NAME_TYPE_3: "Steam Room",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=custom_options,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(custom_options)
    expect(config_entry.options).to_equal(custom_options)


@test
async def options_flow_with_existing_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    saunum_client: MagicMock = Depends(mock_saunum_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test options flow with existing custom preset names."""
    existing_options = {
        OPT_PRESET_NAME_TYPE_1: "My Custom Type 1",
        OPT_PRESET_NAME_TYPE_2: "My Custom Type 2",
        OPT_PRESET_NAME_TYPE_3: "My Custom Type 3",
    }

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_USER_INPUT,
        options=existing_options,
        title="Saunum",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    updated_options = {
        OPT_PRESET_NAME_TYPE_1: "Updated Type 1",
        OPT_PRESET_NAME_TYPE_2: "My Custom Type 2",
        OPT_PRESET_NAME_TYPE_3: "My Custom Type 3",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=updated_options,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(updated_options)
    expect(config_entry.options).to_equal(updated_options)
