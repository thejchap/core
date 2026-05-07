"""Tryke ports of the emoncms config flow tests."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.emoncms.const import (
    CONF_ONLY_INCLUDE_FEEDID,
    DOMAIN,
    SYNC_MODE,
    SYNC_MODE_AUTO,
    SYNC_MODE_MANUAL,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration
from ._fixtures import (
    EMONCMS_FAILURE,
    FLOW_RESULT,
    SENSOR_NAME,
    UNIQUE_ID,
    config_entry,
    config_entry_unique_id,
    config_no_feed,
    config_single_feed,
    emoncms_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


USER_INPUT = {
    CONF_URL: "http://1.1.1.1",
    CONF_API_KEY: "my_api_key",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Module-local fixture-resolution anchor."""


@test.cases(
    test.case(
        "regenerated_api_key",
        url=USER_INPUT[CONF_URL],
        api_key="regenerated_api_key",
    ),
    test.case(
        "different_url",
        url="http://1.1.1.2",
        api_key=USER_INPUT[CONF_API_KEY],
    ),
)
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(emoncms_client),
    *,
    url: str,
    api_key: str,
) -> None:
    """Test reconfigure flow."""
    new_input = {CONF_URL: url, CONF_API_KEY: api_key}
    cfg_entry = MockConfigEntry(
        domain=DOMAIN,
        title=SENSOR_NAME,
        data=new_input,
        unique_id=UNIQUE_ID,
    )
    await setup_integration(hass, cfg_entry)
    result = await cfg_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], new_input
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(cfg_entry.data).to_equal(new_input)


@test
async def reconfigure_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test reconfigure flow with API error."""
    cfg_entry = MockConfigEntry(
        domain=DOMAIN,
        title=SENSOR_NAME,
        data=USER_INPUT,
        unique_id=UNIQUE_ID,
    )
    await setup_integration(hass, cfg_entry)
    client.async_request.return_value = EMONCMS_FAILURE
    result = await cfg_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "api_error"})
    expect(result["description_placeholders"]["details"]).to_equal("failure")
    expect(result["step_id"]).to_equal("reconfigure")


@test
async def user_flow_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test emoncms failure when adding a new entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    client.async_request.return_value = EMONCMS_FAILURE
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    expect(result["errors"]["base"]).to_equal("api_error")
    expect(result["description_placeholders"]["details"]).to_equal("failure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def user_flow_manual_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test we get the user forms and the entry in manual mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, SYNC_MODE: SYNC_MODE_MANUAL}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ONLY_INCLUDE_FEEDID: ["1"]}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(SENSOR_NAME)
    expect(result["data"]).to_equal({**USER_INPUT, CONF_ONLY_INCLUDE_FEEDID: ["1"]})


@test
async def user_flow_auto_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test we get the user form and the entry in automatic mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, SYNC_MODE: SYNC_MODE_AUTO}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(SENSOR_NAME)
    expect(result["data"]).to_equal(
        {
            **USER_INPUT,
            CONF_ONLY_INCLUDE_FEEDID: FLOW_RESULT[CONF_ONLY_INCLUDE_FEEDID],
        }
    )
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(emoncms_client),
    cfg_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Options flow - success test."""
    await setup_integration(hass, cfg_entry)
    expect(cfg_entry.options).to_equal({})
    result = await hass.config_entries.options.async_init(cfg_entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ONLY_INCLUDE_FEEDID: ["1"]},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(cfg_entry.options).to_equal({CONF_ONLY_INCLUDE_FEEDID: ["1"]})


@test
async def options_flow_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(emoncms_client),
    cfg_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Options flow - test failure."""
    await setup_integration(hass, cfg_entry)
    client.async_request.return_value = EMONCMS_FAILURE
    result = await hass.config_entries.options.async_init(cfg_entry.entry_id)
    await hass.async_block_till_done()
    expect(result["errors"]["base"]).to_equal("api_error")
    expect(result["description_placeholders"]["details"]).to_equal("failure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")


@test
async def unique_id_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(emoncms_client),
    cfg_entry_unique_id: MockConfigEntry = Depends(config_entry_unique_id),
) -> None:
    """Test when entry with same unique id already exists."""
    cfg_entry_unique_id.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
