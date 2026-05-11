"""Test for SQL component Init."""

from unittest.mock import patch

import voluptuous as vol

from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder import CONF_DB_URL
from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.sql.const import (
    CONF_ADVANCED_OPTIONS,
    CONF_COLUMN_NAME,
    CONF_QUERY,
    DOMAIN,
)
from homeassistant.components.sql.util import validate_sql_select
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template
from homeassistant.setup import async_setup_component

from . import YAML_CONFIG_INVALID, YAML_CONFIG_NO_DB, init_integration
from ._fixtures import recorder_mock

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup entry."""
    config_entry = await init_integration(hass)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unload an entry."""
    config_entry = await init_integration(hass)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def setup_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from yaml config."""
    with patch(
        "homeassistant.components.sql.config_flow.sqlalchemy.create_engine",
    ):
        expect(
            await async_setup_component(hass, DOMAIN, YAML_CONFIG_NO_DB)
        ).to_be(True)
        await hass.async_block_till_done()


@test
async def setup_invalid_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from yaml with invalid config."""
    with patch(
        "homeassistant.components.sql.config_flow.sqlalchemy.create_engine",
    ):
        expect(
            await async_setup_component(hass, DOMAIN, YAML_CONFIG_INVALID)
        ).to_be(False)
        await hass.async_block_till_done()


@test
async def invalid_query(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid query."""
    expect(
        lambda: validate_sql_select(Template("DROP TABLE *", hass))
    ).to_raise(vol.Invalid, match="SQL query must be of type SELECT")
    expect(
        lambda: validate_sql_select(Template("SELECT5 as value", hass))
    ).to_raise(vol.Invalid, match="SQL query is empty or unknown type")
    expect(
        lambda: validate_sql_select(Template(";;", hass))
    ).to_raise(vol.Invalid, match="SQL query is empty or unknown type")


@test
async def query_no_read_only(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test query no read only."""
    expect(
        lambda: validate_sql_select(
            Template("UPDATE states SET state = 999999 WHERE state_id = 11125", hass)
        )
    ).to_raise(vol.Invalid, match="SQL query must be of type SELECT")


@test
async def query_no_read_only_cte(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test query no read only CTE."""
    expect(
        lambda: validate_sql_select(
            Template(
                "WITH test AS (SELECT state FROM states) "
                "UPDATE states SET states.state = test.state;",
                hass,
            )
        )
    ).to_raise(vol.Invalid, match="SQL query must be of type SELECT")


@test
async def multiple_queries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test multiple queries."""
    expect(
        lambda: validate_sql_select(
            Template("SELECT 5 as value; UPDATE states SET state = 10;", hass)
        )
    ).to_raise(vol.Invalid, match="Multiple SQL statements are not allowed")


@test
async def migration_from_future(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migration from future version fails."""
    config_entry = MockConfigEntry(
        title="Test future",
        domain=DOMAIN,
        source=SOURCE_USER,
        data={},
        options={
            CONF_QUERY: "SELECT 5.01 as value",
            CONF_COLUMN_NAME: "value",
            CONF_ADVANCED_OPTIONS: {},
        },
        entry_id="1",
        version=3,
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)


@test
async def migration_from_v1_to_v2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migration from version 1 to 2."""
    config_entry = MockConfigEntry(
        title="Test migration",
        domain=DOMAIN,
        source=SOURCE_USER,
        data={},
        options={
            CONF_DB_URL: "sqlite://",
            CONF_NAME: "Test migration",
            CONF_QUERY: "SELECT 5.01 as value",
            CONF_COLUMN_NAME: "value",
            CONF_VALUE_TEMPLATE: "{{ value | int }}",
            CONF_UNIT_OF_MEASUREMENT: "MiB",
            CONF_DEVICE_CLASS: SensorDeviceClass.DATA_SIZE,
            CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
        },
        entry_id="1",
        version=1,
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            CONF_QUERY: "SELECT 5.01 as value",
            CONF_COLUMN_NAME: "value",
            CONF_ADVANCED_OPTIONS: {
                CONF_VALUE_TEMPLATE: "{{ value | int }}",
                CONF_UNIT_OF_MEASUREMENT: "MiB",
                CONF_DEVICE_CLASS: SensorDeviceClass.DATA_SIZE,
                CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
            },
        }
    )

    state = hass.states.get("sensor.test_migration")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("5")
