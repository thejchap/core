"""Tests for the file config flow."""

from typing import Any
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.file import DOMAIN
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_is_allowed_path_false,
    mock_is_allowed_path_true,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_CONFIG_NOTIFY = {
    "platform": "notify",
    "file_path": "some_file",
}
MOCK_OPTIONS_NOTIFY = {"timestamp": True}
MOCK_CONFIG_SENSOR = {
    "platform": "sensor",
    "file_path": "some/path",
}
MOCK_OPTIONS_SENSOR = {"value_template": "{{ value | round(1) }}"}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case(
        "sensor",
        platform="sensor",
        data=MOCK_CONFIG_SENSOR,
        options=MOCK_OPTIONS_SENSOR,
    ),
    test.case(
        "notify",
        platform="notify",
        data=MOCK_CONFIG_NOTIFY,
        options=MOCK_OPTIONS_NOTIFY,
    ),
)
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _allowed: object = Depends(mock_is_allowed_path_true),
    *,
    platform: str,
    data: dict[str, Any],
    options: dict[str, Any],
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": platform},
    )
    await hass.async_block_till_done()

    user_input = {**data, **options}
    user_input.pop("platform")
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(data)
    expect(result2["options"]).to_equal(options)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "sensor",
        platform="sensor",
        data=MOCK_CONFIG_SENSOR,
        options=MOCK_OPTIONS_SENSOR,
    ),
    test.case(
        "notify",
        platform="notify",
        data=MOCK_CONFIG_NOTIFY,
        options=MOCK_OPTIONS_NOTIFY,
    ),
)
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _allowed: object = Depends(mock_is_allowed_path_true),
    *,
    platform: str,
    data: dict[str, Any],
    options: dict[str, Any],
) -> None:
    """Test aborting if the entry is already configured."""
    entry = MockConfigEntry(domain=DOMAIN, data=data, options=options)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": platform},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(platform)

    user_input = {**data, **options}
    user_input.pop("platform")
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "sensor",
        platform="sensor",
        data=MOCK_CONFIG_SENSOR,
        options=MOCK_OPTIONS_SENSOR,
    ),
    test.case(
        "notify",
        platform="notify",
        data=MOCK_CONFIG_NOTIFY,
        options=MOCK_OPTIONS_NOTIFY,
    ),
)
async def not_allowed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _not_allowed: object = Depends(mock_is_allowed_path_false),
    *,
    platform: str,
    data: dict[str, Any],
    options: dict[str, Any],
) -> None:
    """Test aborting if the file path is not allowed."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": platform},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(platform)

    user_input = {**data, **options}
    user_input.pop("platform")
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"file_path": "not_allowed"})


@test.cases(
    test.case(
        "sensor",
        platform="sensor",
        data=MOCK_CONFIG_SENSOR,
        options=MOCK_OPTIONS_SENSOR,
        new_options={CONF_UNIT_OF_MEASUREMENT: "mm"},
    ),
    test.case(
        "notify",
        platform="notify",
        data=MOCK_CONFIG_NOTIFY,
        options=MOCK_OPTIONS_NOTIFY,
        new_options={"timestamp": False},
    ),
)
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _allowed: object = Depends(mock_is_allowed_path_true),
    *,
    platform: str,
    data: dict[str, Any],
    options: dict[str, Any],
    new_options: dict[str, Any],
) -> None:
    """Test options config flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=data, options=options, version=2)
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=new_options,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(new_options)

    entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(entry.state).to_be(config_entries.ConfigEntryState.LOADED)
    expect(entry.options).to_equal(new_options)
