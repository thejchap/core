"""Test the sql utils."""

from datetime import UTC, date, datetime
from decimal import Decimal

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder import get_instance
from homeassistant.components.sql.util import (
    convert_value,
    resolve_db_url,
    validate_sql_select,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

from ._fixtures import recorder_mock

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def resolve_db_url_when_none_configured(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _recorder: object = Depends(recorder_mock),
) -> None:
    """Test return recorder db_url if provided db_url is None."""
    db_url = None
    resolved_url = resolve_db_url(hass, db_url)

    expect(resolved_url).to_equal(get_instance(hass).db_url)


@test
async def resolve_db_url_when_configured(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test return provided db_url if it's set."""
    db_url = "mssql://"
    resolved_url = resolve_db_url(hass, db_url)

    expect(resolved_url).to_equal(db_url)


@test.cases(
    test.case(
        "drop_table",
        sql_query="DROP TABLE *",
        expected_error_message="SQL query must be of type SELECT",
    ),
    test.case(
        "select_no_space",
        sql_query="SELECT5 as value",
        expected_error_message="SQL query is empty or unknown type",
    ),
    test.case(
        "empty_semicolons",
        sql_query=";;",
        expected_error_message="SQL query is empty or unknown type",
    ),
    test.case(
        "update_query",
        sql_query="UPDATE states SET state = 999999 WHERE state_id = 11125",
        expected_error_message="SQL query must be of type SELECT",
    ),
    test.case(
        "with_then_update",
        sql_query=(
            "WITH test AS (SELECT state FROM states) "
            "UPDATE states SET states.state = test.state;"
        ),
        expected_error_message="SQL query must be of type SELECT",
    ),
    test.case(
        "multiple_statements",
        sql_query="SELECT 5 as value; UPDATE states SET state = 10;",
        expected_error_message="Multiple SQL statements are not allowed",
    ),
)
async def invalid_sql_queries(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    sql_query: str,
    expected_error_message: str,
) -> None:
    """Test that various invalid or disallowed SQL queries raise the correct exception."""
    async with expect_raises_async(vol.Invalid, match=expected_error_message):
        validate_sql_select(Template(sql_query, hass))


@test.cases(
    test.case("decimal", input=Decimal("199.99"), expected_output=199.99),
    test.case("date", input=date(2023, 1, 15), expected_output="2023-01-15"),
    test.case(
        "datetime",
        input=datetime(2023, 1, 15, 12, 30, 45, tzinfo=UTC),
        expected_output="2023-01-15T12:30:45+00:00",
    ),
    test.case("bytes", input=b"\xde\xad\xbe\xef", expected_output="0xdeadbeef"),
    test.case("str", input="deadbeef", expected_output="deadbeef"),
    test.case("float", input=199.99, expected_output=199.99),
    test.case("int", input=69, expected_output=69),
)
async def value_conversion(
    _t: HomeAssistant = Depends(_trigger_executor),
    *,
    input: Decimal | date | datetime | bytes | str | float,
    expected_output: str | float,
) -> None:
    """Test value conversion."""
    expect(convert_value(input)).to_equal(expected_output)
