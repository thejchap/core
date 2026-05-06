"""Test the SQL config flow."""

from tryke import test


@test.skip("requires recorder_mock fixture")
async def form_simple() -> None:
    """Test form simple."""


@test.skip("requires recorder_mock fixture")
async def form_with_query_template() -> None:
    """Test form with query template."""


@test.skip("requires recorder_mock fixture")
async def form_with_broken_query_template() -> None:
    """Test form with broken query template."""


@test.skip("requires recorder_mock fixture")
async def form_with_value_template() -> None:
    """Test form with value template."""


@test.skip("requires recorder_mock fixture")
async def flow_fails_db_url() -> None:
    """Test flow fails on db url."""


@test.skip("requires recorder_mock fixture")
async def flow_fails_invalid_query() -> None:
    """Test flow fails invalid query."""


@test.skip("requires recorder_mock fixture")
async def flow_fails_invalid_column_name() -> None:
    """Test flow fails invalid column name."""


@test.skip("requires recorder_mock fixture")
async def options_flow() -> None:
    """Test options flow."""


@test.skip("requires recorder_mock fixture")
async def options_flow_name_previously_removed() -> None:
    """Test options flow name previously removed."""


@test.skip("requires recorder_mock fixture")
async def options_flow_fails_db_url() -> None:
    """Test options flow fails on db url."""


@test.skip("requires recorder_mock fixture")
async def options_flow_fails_invalid_query() -> None:
    """Test options flow fails invalid query."""


@test.skip("requires recorder_mock fixture")
async def options_flow_fails_invalid_column_name() -> None:
    """Test options flow fails invalid column name."""


@test.skip("requires recorder_mock fixture")
async def options_flow_db_url_empty() -> None:
    """Test options flow with empty db url."""


@test.skip("requires recorder_mock fixture")
async def full_flow_not_recorder_db() -> None:
    """Test full flow with not recorder db."""


@test.skip("requires recorder_mock fixture")
async def device_state_class() -> None:
    """Test device state class options."""
