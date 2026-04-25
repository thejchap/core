"""Test the Suez Water config flow."""

from unittest.mock import AsyncMock

from pysuez.exception import PySuezError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.suez_water.const import CONF_COUNTER_ID, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import MOCK_DATA, mock_setup_entry, suez_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(suez_client),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_DATA[CONF_COUNTER_ID])
    expect(result["result"].unique_id).to_equal(MOCK_DATA[CONF_COUNTER_ID])
    expect(result["data"]).to_equal(MOCK_DATA)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(suez_client),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    client.check_credentials.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    client.check_credentials.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_DATA,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_DATA[CONF_COUNTER_ID])
    expect(result["result"].unique_id).to_equal(MOCK_DATA[CONF_COUNTER_ID])
    expect(result["data"]).to_equal(MOCK_DATA)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.skip("requires recorder_mock")
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort when entry is already configured."""


@test.cases(
    test.case("cannot_connect", exception=PySuezError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def form_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(suez_client),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    client.check_credentials.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.check_credentials.return_value = True
    client.check_credentials.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_DATA[CONF_COUNTER_ID])
    expect(result["data"]).to_equal(MOCK_DATA)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_auto_counter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(suez_client),
) -> None:
    """Test form set counter if not set by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    partial_form = MOCK_DATA.copy()
    partial_form.pop(CONF_COUNTER_ID)
    client.find_counter.side_effect = PySuezError("test counter not found")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        partial_form,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "counter_not_found"})

    client.find_counter.side_effect = None
    client.find_counter.return_value = MOCK_DATA[CONF_COUNTER_ID]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        partial_form,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(MOCK_DATA[CONF_COUNTER_ID])
    expect(result["result"].unique_id).to_equal(MOCK_DATA[CONF_COUNTER_ID])
    expect(result["data"]).to_equal(MOCK_DATA)
    expect(len(setup_entry.mock_calls)).to_equal(1)
