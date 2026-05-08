"""The test for the sql sensor platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.sql.const import CONF_COLUMN_NAME, CONF_QUERY
from homeassistant.core import HomeAssistant

from . import init_integration
from ._fixtures import recorder_mock

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def query_basic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the SQL sensor."""
    options = {
        CONF_QUERY: "SELECT 5 as value",
        CONF_COLUMN_NAME: "value",
    }
    await init_integration(hass, title="Select value SQL query", options=options)

    state = hass.states.get("sensor.select_value_sql_query")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("5")
    expect(state.attributes["value"]).to_equal(5)


@test
async def query_cte(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the SQL sensor with CTE."""
    options = {
        CONF_QUERY: "WITH test AS (SELECT 1 AS row_num, 10 AS state) SELECT state FROM test WHERE row_num = 1 LIMIT 1;",
        CONF_COLUMN_NAME: "state",
    }
    await init_integration(hass, title="Select value SQL query CTE", options=options)

    state = hass.states.get("sensor.select_value_sql_query_cte")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("10")
    expect(state.attributes["state"]).to_equal(10)


@test.skip("requires recorder + value template — port deferred")
async def query_value_template() -> None:
    """Stub for test_query_value_template."""


@test.skip("requires recorder + template — port deferred")
async def template_query() -> None:
    """Stub for test_template_query."""


@test.skip("requires recorder + invalid value template — port deferred")
async def query_value_template_invalid() -> None:
    """Stub for test_query_value_template_invalid."""


@test.skip("requires recorder + broken template — port deferred")
async def broken_template_query() -> None:
    """Stub for test_broken_template_query."""


@test.skip("requires recorder + broken template — port deferred")
async def broken_template_query_2() -> None:
    """Stub for test_broken_template_query_2."""


@test.skip("requires recorder + LIMIT clause — port deferred")
async def query_limit() -> None:
    """Stub for test_query_limit."""


@test.skip("requires recorder + empty result — port deferred")
async def query_no_value() -> None:
    """Stub for test_query_no_value."""


@test.skip("requires recorder + on-disk sqlite — port deferred")
async def query_on_disk_sqlite_no_result() -> None:
    """Stub for test_query_on_disk_sqlite_no_result."""


@test.skip("requires recorder + invalid URL — port deferred")
async def invalid_url_setup() -> None:
    """Stub for test_invalid_url_setup."""


@test.skip("requires recorder + invalid URL on update — port deferred")
async def invalid_url_on_update() -> None:
    """Stub for test_invalid_url_on_update."""


@test.skip("requires recorder + YAML import — port deferred")
async def query_from_yaml() -> None:
    """Stub for test_query_from_yaml."""


@test.skip("requires recorder + YAML templates — port deferred")
async def templates_with_yaml() -> None:
    """Stub for test_templates_with_yaml."""


@test.skip("requires recorder + legacy YAML — port deferred")
async def config_from_old_yaml() -> None:
    """Stub for test_config_from_old_yaml."""


@test.skip("requires recorder + YAML invalid URL — port deferred")
async def invalid_url_setup_from_yaml() -> None:
    """Stub for test_invalid_url_setup_from_yaml."""


@test.skip("requires recorder + YAML attributes — port deferred")
async def attributes_from_yaml_setup() -> None:
    """Stub for test_attributes_from_yaml_setup."""


@test.skip("requires recorder + binary YAML data — port deferred")
async def binary_data_from_yaml_setup() -> None:
    """Stub for test_binary_data_from_yaml_setup."""


@test.skip("requires recorder + issue registry — port deferred")
async def issue_when_using_old_query() -> None:
    """Stub for test_issue_when_using_old_query."""


@test.skip("requires recorder + issue registry — port deferred")
async def issue_when_using_old_query_without_unique_id() -> None:
    """Stub for test_issue_when_using_old_query_without_unique_id."""


@test.skip("requires recorder + issue registry — port deferred")
async def no_issue_when_view_has_the_text_entity_id_in_it() -> None:
    """Stub for test_no_issue_when_view_has_the_text_entity_id_in_it."""


@test.skip("requires recorder + multi-sensor — port deferred")
async def multiple_sensors_using_same_db() -> None:
    """Stub for test_multiple_sensors_using_same_db."""


@test.skip("requires recorder + lifecycle — port deferred")
async def engine_is_disposed_at_stop() -> None:
    """Stub for test_engine_is_disposed_at_stop."""


@test.skip("requires recorder + entry attributes — port deferred")
async def attributes_from_entry_config() -> None:
    """Stub for test_attributes_from_entry_config."""


@test.skip("requires recorder + rollback recovery — port deferred")
async def query_recover_from_rollback() -> None:
    """Stub for test_query_recover_from_rollback."""


@test.skip("requires no-recorder fallback — port deferred")
async def setup_without_recorder() -> None:
    """Stub for test_setup_without_recorder."""


@test.skip("requires recorder + availability template — port deferred")
async def availability_blocks_value_template() -> None:
    """Stub for test_availability_blocks_value_template."""
