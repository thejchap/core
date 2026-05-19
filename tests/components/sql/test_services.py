"""Tests for the SQL integration services."""

from pathlib import Path
import sqlite3
from unittest.mock import patch

import voluptuous as vol
from voluptuous import MultipleInvalid

from tryke import Depends, expect, fixture, test

from homeassistant.components.sql.const import DOMAIN
from homeassistant.components.sql.services import SERVICE_QUERY
from homeassistant.components.sql.util import generate_lambda_stmt
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.setup import async_setup_component

from ._fixtures import recorder_mock

from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Force tryke fixture resolution before each test."""


@fixture
def _trigger_executor_with_recorder(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
) -> None:
    """Force tryke fixture resolution (with recorder) before each test."""


@test
async def query_service_recorder_db(
    _trigger: None = Depends(_trigger_executor_with_recorder),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the query service with the default recorder database."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    hass.states.async_set("sensor.test", "123", {"attr": "value"})
    hass.states.async_set("sensor.test2", "456")
    await async_wait_recording_done(hass)

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_QUERY,
        {
            "query": (
                "SELECT states_meta.entity_id, states.state "
                "FROM states INNER JOIN states_meta ON states.metadata_id = states_meta.metadata_id "
                "WHERE states_meta.entity_id LIKE 'sensor.test%' ORDER BY states_meta.entity_id"
            )
        },
        blocking=True,
        return_response=True,
    )

    expect(response).to_equal(
        {
            "result": [
                {"entity_id": "sensor.test", "state": "123"},
                {"entity_id": "sensor.test2", "state": "456"},
            ]
        }
    )


@test
async def query_service_external_db(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test the query service with an external database via db_url."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (name TEXT, age INTEGER)")
    conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30), ('Bob', 25)")
    conn.commit()
    conn.close()

    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_QUERY,
        {"query": "SELECT name, age FROM users ORDER BY age", "db_url": db_url},
        blocking=True,
        return_response=True,
    )

    expect(response).to_equal(
        {
            "result": [
                {"name": "Bob", "age": 25},
                {"name": "Alice", "age": 30},
            ]
        }
    )


@test
async def query_service_rollback_on_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the query service."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    with (
        patch(
            "homeassistant.components.sql.services.generate_lambda_stmt",
            return_value=generate_lambda_stmt("Faulty syntax create operational issue"),
        ),
        patch("sqlalchemy.orm.session.Session.rollback") as mock_session_rollback,
    ):
        async with expect_raises_async(
            ServiceValidationError, match="An error occurred when executing the query"
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_QUERY,
                {
                    "query": "SELECT name, age FROM users ORDER BY age",
                    "db_url": "sqlite:///",
                },
                blocking=True,
                return_response=True,
            )

    mock_session_rollback.assert_called_once()


@test
async def query_service_data_conversion(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test the query service correctly converts data types."""
    db_path = tmp_path / "test_types.db"
    db_url = f"sqlite:///{db_path}"

    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE data (id INTEGER, cost DECIMAL(10, 2), event_date DATE, raw BLOB)"
    )
    conn.execute(
        "INSERT INTO data (id, cost, event_date, raw) VALUES (1, 199.99, '2023-01-15', X'DEADBEEF')"
    )
    conn.commit()
    conn.close()

    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_QUERY,
        {"query": "SELECT * FROM data", "db_url": db_url},
        blocking=True,
        return_response=True,
    )

    expect(response).to_equal(
        {
            "result": [
                {
                    "id": 1,
                    "cost": 199.99,
                    "event_date": "2023-01-15",
                    "raw": "0xdeadbeef",
                }
            ]
        }
    )


@test
async def query_service_no_results(
    _trigger: None = Depends(_trigger_executor_with_recorder),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the query service when a query returns no results."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_QUERY,
        {"query": "SELECT * FROM states"},
        blocking=True,
        return_response=True,
    )

    expect(response).to_equal({"result": []})


@test
async def query_service_invalid_query_not_select(
    _trigger: None = Depends(_trigger_executor_with_recorder),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the service rejects non-SELECT queries."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    async with expect_raises_async(vol.Invalid, match="SQL query must be of type SELECT"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_QUERY,
            {"query": "UPDATE states SET state = 'hacked'"},
            blocking=True,
            return_response=True,
        )


@test
async def query_service_sqlalchemy_error(
    _trigger: None = Depends(_trigger_executor_with_recorder),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the service handles SQLAlchemy errors during query execution."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    async with expect_raises_async(
        MultipleInvalid, match="SQL query is empty or unknown type"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_QUERY,
            {"query": "SELEC * FROM states"},
            blocking=True,
            return_response=True,
        )


@test
async def query_service_invalid_db_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the service handles an invalid database URL."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.sql.util._validate_and_get_session_maker_for_db_url",
        return_value=None,
    ):
        async with expect_raises_async(
            ServiceValidationError, match="Failed to connect to the database"
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_QUERY,
                {
                    "query": "SELECT 1",
                    "db_url": "postgresql://user:pass@host:123/dbname",
                },
                blocking=True,
                return_response=True,
            )


@test
async def query_service_performance_issue_validation(
    _trigger: None = Depends(_trigger_executor_with_recorder),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the service validates queries against the recorder for performance issues."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    async with expect_raises_async(
        ServiceValidationError,
        match="The provided query is not allowed: Query contains entity_id but does not reference states_meta",
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_QUERY,
            {"query": "SELECT entity_id FROM states"},
            blocking=True,
            return_response=True,
        )
