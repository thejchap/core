"""Test emoncms config flow."""

from unittest.mock import AsyncMock, MagicMock

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

from tests.common import MockConfigEntry
from tests.components.emoncms import setup_integration
from tests.components.emoncms._fixtures import (
    EMONCMS_FAILURE,
    FLOW_RESULT,
    SENSOR_NAME,
    UNIQUE_ID,
    config_entry,
    config_entry_unique_id,
    emoncms_client,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network

USER_INPUT = {
    CONF_URL: "http://1.1.1.1",
    CONF_API_KEY: "my_api_key",
}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("regenerated_api_key", USER_INPUT[CONF_URL], "regenerated_api_key"),
    test.case("new_url", "http://1.1.1.2", USER_INPUT[CONF_API_KEY]),
)
async def reconfigure(
    url: str,
    api_key: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _emoncms_client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test reconfigure flow."""
    new_input = {
        CONF_URL: url,
        CONF_API_KEY: api_key,
    }
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title=SENSOR_NAME,
        data=new_input,
        unique_id=UNIQUE_ID,
    )
    await setup_integration(hass, config_entry)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        new_input,
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal(new_input)


@test
async def reconfigure_api_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    emoncms_client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test reconfigure flow with API error."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title=SENSOR_NAME,
        data=USER_INPUT,
        unique_id=UNIQUE_ID,
    )
    await setup_integration(hass, config_entry)
    emoncms_client.async_request.return_value = EMONCMS_FAILURE
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "api_error"})
    expect(result["description_placeholders"]["details"]).to_equal("failure")
    expect(result["step_id"]).to_equal("reconfigure")


@test
async def user_flow_failure(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    emoncms_client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test emoncms failure when adding a new entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    emoncms_client.async_request.return_value = EMONCMS_FAILURE
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["errors"]["base"]).to_equal("api_error")
    expect(result["description_placeholders"]["details"]).to_equal("failure")
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")


@test
async def user_flow_manual_mode(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _emoncms_client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test we get the user forms and the entry in manual mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**USER_INPUT, SYNC_MODE: SYNC_MODE_MANUAL},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ONLY_INCLUDE_FEEDID: ["1"]},
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(SENSOR_NAME)
    expect(result["data"]).to_equal({**USER_INPUT, CONF_ONLY_INCLUDE_FEEDID: ["1"]})


@test
async def user_flow_auto_mode(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _emoncms_client: AsyncMock = Depends(emoncms_client),
) -> None:
    """Test we get the user form and the entry in automatic mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**USER_INPUT, SYNC_MODE: SYNC_MODE_AUTO},
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(SENSOR_NAME)
    expect(result["data"]).to_equal(
        {
            **USER_INPUT,
            CONF_ONLY_INCLUDE_FEEDID: FLOW_RESULT[CONF_ONLY_INCLUDE_FEEDID],
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _emoncms_client: AsyncMock = Depends(emoncms_client),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Options flow - success test."""
    await setup_integration(hass, config_entry)
    expect(config_entry.options).to_equal({})
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ONLY_INCLUDE_FEEDID: ["1"],
        },
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(config_entry.options).to_equal(
        {
            CONF_ONLY_INCLUDE_FEEDID: ["1"],
        }
    )


@test
async def options_flow_failure(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    emoncms_client: AsyncMock = Depends(emoncms_client),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Options flow - test failure."""
    await setup_integration(hass, config_entry)
    emoncms_client.async_request.return_value = EMONCMS_FAILURE
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(result["errors"]["base"]).to_equal("api_error")
    expect(result["description_placeholders"]["details"]).to_equal("failure")
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")


@test
async def unique_id_exists(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _emoncms_client: AsyncMock = Depends(emoncms_client),
    config_entry_unique_id: MockConfigEntry = Depends(config_entry_unique_id),
) -> None:
    """Test when entry with same unique id already exists."""
    config_entry_unique_id.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
