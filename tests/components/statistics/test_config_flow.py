"""Test the Statistics config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.statistics import DOMAIN
from homeassistant.components.statistics.sensor import (
    CONF_KEEP_LAST_SAMPLE,
    CONF_MAX_AGE,
    CONF_PERCENTILE,
    CONF_PRECISION,
    CONF_SAMPLES_MAX_BUFFER_SIZE,
    CONF_STATE_CHARACTERISTIC,
    DEFAULT_NAME,
    STAT_AVERAGE_LINEAR,
    STAT_COUNT,
)
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture to force tryke to resolve dependencies."""


@test
async def form_sensor(
    _trigger: None = Depends(_trigger_executor),
    setup: AsyncMock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form for sensor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test_monitored",
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STATE_CHARACTERISTIC: STAT_AVERAGE_LINEAR,
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
            CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["version"]).to_equal(1)
    expect(result["options"]).to_equal(
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test_monitored",
            CONF_STATE_CHARACTERISTIC: STAT_AVERAGE_LINEAR,
            CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
            CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
            CONF_KEEP_LAST_SAMPLE: False,
            CONF_PERCENTILE: 50.0,
            CONF_PRECISION: 2.0,
        }
    )

    expect(len(setup.mock_calls)).to_equal(1)


@test
async def form_binary_sensor(
    _trigger: None = Depends(_trigger_executor),
    setup: AsyncMock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form for binary sensor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "binary_sensor.test_monitored",
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STATE_CHARACTERISTIC: STAT_COUNT,
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
            CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["version"]).to_equal(1)
    expect(result["options"]).to_equal(
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "binary_sensor.test_monitored",
            CONF_STATE_CHARACTERISTIC: STAT_COUNT,
            CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
            CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
            CONF_KEEP_LAST_SAMPLE: False,
            CONF_PERCENTILE: 50.0,
            CONF_PRECISION: 2.0,
        }
    )

    expect(len(setup.mock_calls)).to_equal(1)


@test
async def validation_options(
    _trigger: None = Depends(_trigger_executor),
    setup: AsyncMock = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test validation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test_monitored",
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STATE_CHARACTERISTIC: STAT_AVERAGE_LINEAR,
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()

    expect(result["step_id"]).to_equal("options")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "missing_max_age_or_sampling_size"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_KEEP_LAST_SAMPLE: True, CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0},
    )
    await hass.async_block_till_done()

    expect(result["step_id"]).to_equal("options")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "missing_keep_last_sample"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
            CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["version"]).to_equal(1)
    expect(result["options"]).to_equal(
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test_monitored",
            CONF_STATE_CHARACTERISTIC: STAT_AVERAGE_LINEAR,
            CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
            CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
            CONF_KEEP_LAST_SAMPLE: False,
            CONF_PERCENTILE: 50.0,
            CONF_PRECISION: 2.0,
        }
    )

    expect(len(setup.mock_calls)).to_equal(1)


@test.skip("loaded_entry fixture depends on recorder_mock + VALUES_NUMERIC from test_sensor")
async def options_flow() -> None:
    """Skipped pending recorder_mock fixture."""


@test.skip("loaded_entry fixture depends on recorder_mock + VALUES_NUMERIC from test_sensor")
async def entry_already_exist() -> None:
    """Skipped pending recorder_mock fixture."""


@test.skip("requires recorder_mock + hass_ws_client + snapshot fixtures")
async def config_flow_preview_success() -> None:
    """Skipped pending recorder_mock fixture."""


@test.skip("requires recorder_mock + hass_ws_client + snapshot fixtures")
async def options_flow_preview() -> None:
    """Skipped pending recorder_mock fixture."""


@test.skip("requires recorder_mock + hass_ws_client fixtures")
async def options_flow_sensor_preview_config_entry_removed() -> None:
    """Skipped pending recorder_mock fixture."""
