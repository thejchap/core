"""Tryke skip-stubs for SQL test_sensor."""

from tryke import test


@test.skip("requires recorder + sensor — port deferred")
async def query_basic() -> None:
    """Stub for test_query_basic."""


@test.skip("requires recorder + CTE query — port deferred")
async def query_cte() -> None:
    """Stub for test_query_cte."""


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
