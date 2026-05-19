"""Test util methods (tryke port)."""

from contextlib import AbstractContextManager, nullcontext as does_not_raise
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from sqlalchemy.exc import OperationalError
from tryke import expect, test

from homeassistant.components.recorder import util
from homeassistant.components.recorder.const import SupportedDialect
from homeassistant.components.recorder.models import UnsupportedDialect
from homeassistant.components.recorder.util import (
    MIN_VERSION_SQLITE,
    RETRYABLE_MYSQL_ERRORS,
    database_job_retry_wrapper,
    is_second_sunday,
    retryable_database_job,
    retryable_database_job_method,
)
from homeassistant.util import dt as dt_util


@test
def is_second_sunday_test() -> None:
    """Test we can find the second sunday of the month."""
    expect(
        is_second_sunday(datetime(2022, 1, 9, 0, 0, 0, tzinfo=dt_util.UTC))
    ).to_be(True)
    expect(
        is_second_sunday(datetime(2022, 2, 13, 0, 0, 0, tzinfo=dt_util.UTC))
    ).to_be(True)
    expect(
        is_second_sunday(datetime(2022, 3, 13, 0, 0, 0, tzinfo=dt_util.UTC))
    ).to_be(True)
    expect(
        is_second_sunday(datetime(2022, 4, 10, 0, 0, 0, tzinfo=dt_util.UTC))
    ).to_be(True)
    expect(
        is_second_sunday(datetime(2022, 5, 8, 0, 0, 0, tzinfo=dt_util.UTC))
    ).to_be(True)

    expect(
        is_second_sunday(datetime(2022, 1, 10, 0, 0, 0, tzinfo=dt_util.UTC))
    ).to_be(False)


@test
def build_mysqldb_conv_test() -> None:
    """Test building the MySQLdb connect conv param."""
    mock_converters = Mock(conversions={"original": "preserved"})
    mock_constants = Mock(FIELD_TYPE=Mock(DATETIME="DATETIME"))
    with patch.dict(
        "sys.modules",
        **{"MySQLdb.constants": mock_constants, "MySQLdb.converters": mock_converters},
    ):
        conv = util.build_mysqldb_conv()

    expect(conv["original"]).to_equal("preserved")
    expect(conv["DATETIME"]("INVALID")).to_be(None)
    expect(conv["DATETIME"]("2022-05-13T22:33:12.741")).to_equal(
        datetime(2022, 5, 13, 22, 33, 12, 741000, tzinfo=None)
    )


def _make_mysql_cursor_mock(mysql_version: str) -> tuple[list[str], MagicMock]:
    """Build a dbapi connection mock that returns the given mysql version."""
    execute_args: list[str] = []
    close_mock = MagicMock()

    def execute_mock(statement: str) -> None:
        execute_args.append(statement)

    def fetchall_mock() -> Any:
        if execute_args[-1] == "SELECT VERSION()":
            return [[mysql_version]]
        return None

    def _make_cursor_mock(*_: Any) -> MagicMock:
        return MagicMock(execute=execute_mock, close=close_mock, fetchall=fetchall_mock)

    return execute_args, MagicMock(cursor=_make_cursor_mock)


def _make_pg_cursor_mock(pgsql_version: str) -> tuple[list[str], MagicMock]:
    """Build a dbapi connection mock that returns the given pgsql version."""
    execute_args: list[str] = []
    close_mock = MagicMock()

    def execute_mock(statement: str) -> None:
        execute_args.append(statement)

    def fetchall_mock() -> Any:
        if execute_args[-1] == "SHOW server_version":
            return [[pgsql_version]]
        return None

    def _make_cursor_mock(*_: Any) -> MagicMock:
        return MagicMock(execute=execute_mock, close=close_mock, fetchall=fetchall_mock)

    return execute_args, MagicMock(cursor=_make_cursor_mock)


def _make_sqlite_cursor_mock(sqlite_version: str) -> tuple[list[str], MagicMock]:
    """Build a dbapi connection mock that returns the given sqlite version."""
    execute_args: list[str] = []
    close_mock = MagicMock()

    def execute_mock(statement: str) -> None:
        execute_args.append(statement)

    def fetchall_mock() -> Any:
        if execute_args[-1] == "SELECT sqlite_version()":
            return [[sqlite_version]]
        return None

    def _make_cursor_mock(*_: Any) -> MagicMock:
        return MagicMock(execute=execute_mock, close=close_mock, fetchall=fetchall_mock)

    return execute_args, MagicMock(cursor=_make_cursor_mock)


@test.cases(
    test.case("mariadb_10_3", mysql_version="10.3.0-MariaDB"),
    test.case("mysql_8_0_0", mysql_version="8.0.0"),
)
def setup_connection_for_dialect_mysql(mysql_version: str) -> None:
    """Test setting up the connection for a mysql dialect."""
    instance_mock = MagicMock()
    execute_args, dbapi_connection = _make_mysql_cursor_mock(mysql_version)

    util.setup_connection_for_dialect(instance_mock, "mysql", dbapi_connection, True)

    expect(len(execute_args)).to_be(3)
    expect(execute_args[0]).to_equal("SET session wait_timeout=28800")
    expect(execute_args[1]).to_equal("SELECT VERSION()")
    expect(execute_args[2]).to_equal("SET time_zone = '+00:00'")


@test
def setup_connection_for_dialect_sqlite_test() -> None:
    """Test setting up the connection for a sqlite dialect."""
    sqlite_version = str(MIN_VERSION_SQLITE)
    instance_mock = MagicMock()
    execute_args, dbapi_connection = _make_sqlite_cursor_mock(sqlite_version)

    expect(
        util.setup_connection_for_dialect(
            instance_mock, "sqlite", dbapi_connection, True
        )
        is not None
    ).to_be(True)

    expect(len(execute_args)).to_be(5)
    expect(execute_args[0]).to_equal("PRAGMA journal_mode=WAL")
    expect(execute_args[1]).to_equal("SELECT sqlite_version()")
    expect(execute_args[2]).to_equal("PRAGMA cache_size = -16384")
    expect(execute_args[3]).to_equal("PRAGMA synchronous=NORMAL")
    expect(execute_args[4]).to_equal("PRAGMA foreign_keys=ON")

    execute_args.clear()
    expect(
        util.setup_connection_for_dialect(
            instance_mock, "sqlite", dbapi_connection, False
        )
        is None
    ).to_be(True)

    expect(len(execute_args)).to_be(3)
    expect(execute_args[0]).to_equal("PRAGMA cache_size = -16384")
    expect(execute_args[1]).to_equal("PRAGMA synchronous=NORMAL")
    expect(execute_args[2]).to_equal("PRAGMA foreign_keys=ON")


@test
def setup_connection_for_dialect_sqlite_zero_commit_interval_test() -> None:
    """Test setting up the connection for a sqlite dialect with a zero commit interval."""
    sqlite_version = str(MIN_VERSION_SQLITE)
    instance_mock = MagicMock(commit_interval=0)
    execute_args, dbapi_connection = _make_sqlite_cursor_mock(sqlite_version)

    expect(
        util.setup_connection_for_dialect(
            instance_mock, "sqlite", dbapi_connection, True
        )
        is not None
    ).to_be(True)

    expect(len(execute_args)).to_be(5)
    expect(execute_args[0]).to_equal("PRAGMA journal_mode=WAL")
    expect(execute_args[1]).to_equal("SELECT sqlite_version()")
    expect(execute_args[2]).to_equal("PRAGMA cache_size = -16384")
    expect(execute_args[3]).to_equal("PRAGMA synchronous=FULL")
    expect(execute_args[4]).to_equal("PRAGMA foreign_keys=ON")

    execute_args.clear()
    expect(
        util.setup_connection_for_dialect(
            instance_mock, "sqlite", dbapi_connection, False
        )
        is None
    ).to_be(True)

    expect(len(execute_args)).to_be(3)
    expect(execute_args[0]).to_equal("PRAGMA cache_size = -16384")
    expect(execute_args[1]).to_equal("PRAGMA synchronous=FULL")
    expect(execute_args[2]).to_equal("PRAGMA foreign_keys=ON")


@test.cases(
    test.case("mariadb_10_2_0", mysql_version="10.2.0-MariaDB"),
    test.case("mysql_5_7_26", mysql_version="5.7.26-0ubuntu0.18.04.1"),
    test.case("garbage", mysql_version="some_random_response"),
)
def fail_outdated_mysql(mysql_version: str) -> None:
    """Test setting up the connection for an outdated mysql version."""
    instance_mock = MagicMock()
    _execute_args, dbapi_connection = _make_mysql_cursor_mock(mysql_version)

    expect(
        lambda: util.setup_connection_for_dialect(
            instance_mock, "mysql", dbapi_connection, True
        )
    ).to_raise(UnsupportedDialect)


@test.cases(
    test.case("mariadb_10_3_0", mysql_version="10.3.0"),
    test.case("mysql_8_0_0", mysql_version="8.0.0"),
)
def supported_mysql(mysql_version: str) -> None:
    """Test setting up the connection for a supported mysql version."""
    instance_mock = MagicMock()
    _execute_args, dbapi_connection = _make_mysql_cursor_mock(mysql_version)

    database_engine = util.setup_connection_for_dialect(
        instance_mock, "mysql", dbapi_connection, True
    )
    expect(database_engine is not None).to_be(True)
    expect(database_engine.optimizer.slow_range_in_select).to_be(False)
    expect(database_engine.optimizer.slow_dependent_subquery).to_be(True)


@test.cases(
    test.case("pg_11_12", pgsql_version="11.12 (Debian 11.12-1.pgdg100+1)"),
    test.case("pg_9_2_10", pgsql_version="9.2.10"),
    test.case("garbage", pgsql_version="unexpected"),
)
def fail_outdated_pgsql(pgsql_version: str) -> None:
    """Test setting up the connection for an outdated PostgreSQL version."""
    instance_mock = MagicMock()
    _execute_args, dbapi_connection = _make_pg_cursor_mock(pgsql_version)

    expect(
        lambda: util.setup_connection_for_dialect(
            instance_mock, "postgresql", dbapi_connection, True
        )
    ).to_raise(UnsupportedDialect)


@test
def supported_pgsql_test() -> None:
    """Test setting up the connection for a supported PostgreSQL version."""
    instance_mock = MagicMock()
    _execute_args, dbapi_connection = _make_pg_cursor_mock(
        "14.0 (Debian 14.0-1.pgdg110+1)"
    )

    database_engine = util.setup_connection_for_dialect(
        instance_mock, "postgresql", dbapi_connection, True
    )
    expect(database_engine is not None).to_be(True)
    expect(database_engine.optimizer.slow_range_in_select).to_be(True)
    expect(database_engine.optimizer.slow_dependent_subquery).to_be(False)


@test.cases(
    test.case("sqlite_3_30_0", sqlite_version="3.30.0"),
    test.case("sqlite_2_0_0", sqlite_version="2.0.0"),
)
def fail_outdated_sqlite(sqlite_version: str) -> None:
    """Test setting up the connection for an outdated sqlite version."""
    instance_mock = MagicMock()
    _execute_args, dbapi_connection = _make_sqlite_cursor_mock(sqlite_version)

    expect(
        lambda: util.setup_connection_for_dialect(
            instance_mock, "sqlite", dbapi_connection, True
        )
    ).to_raise(UnsupportedDialect)


@test.cases(
    test.case("sqlite_3_40_1", sqlite_version="3.40.1"),
    test.case("sqlite_3_41_0", sqlite_version="3.41.0"),
)
def supported_sqlite(sqlite_version: str) -> None:
    """Test setting up the connection for a supported sqlite version."""
    instance_mock = MagicMock()
    _execute_args, dbapi_connection = _make_sqlite_cursor_mock(sqlite_version)

    database_engine = util.setup_connection_for_dialect(
        instance_mock, "sqlite", dbapi_connection, True
    )
    expect(database_engine is not None).to_be(True)
    expect(database_engine.optimizer.slow_range_in_select).to_be(False)
    expect(database_engine.optimizer.slow_dependent_subquery).to_be(False)


@test.cases(
    test.case("mssql", dialect="mssql"),
    test.case("oracle", dialect="oracle"),
    test.case("other", dialect="some_db"),
)
def warn_unsupported_dialect(dialect: str) -> None:
    """Test setting up the connection for an unsupported dialect."""
    instance_mock = MagicMock()
    dbapi_connection = MagicMock()

    expect(
        lambda: util.setup_connection_for_dialect(
            instance_mock, dialect, dbapi_connection, True
        )
    ).to_raise(UnsupportedDialect)


NonRetryable = OperationalError(None, None, BaseException())
Retryable = OperationalError(None, None, BaseException(RETRYABLE_MYSQL_ERRORS[0], ""))


@test.cases(
    test.case(
        "mysql_ok",
        side_effect=None,
        dialect=SupportedDialect.MYSQL,
        retval=None,
        expected_exc=None,
        num_calls=1,
    ),
    test.case(
        "mysql_valueerror",
        side_effect=ValueError,
        dialect=SupportedDialect.MYSQL,
        retval=None,
        expected_exc=ValueError,
        num_calls=1,
    ),
    test.case(
        "mysql_non_retryable",
        side_effect=NonRetryable,
        dialect=SupportedDialect.MYSQL,
        retval=None,
        expected_exc=OperationalError,
        num_calls=1,
    ),
    test.case(
        "mysql_retryable",
        side_effect=Retryable,
        dialect=SupportedDialect.MYSQL,
        retval=None,
        expected_exc=OperationalError,
        num_calls=5,
    ),
    test.case(
        "sqlite_non_retryable",
        side_effect=NonRetryable,
        dialect=SupportedDialect.SQLITE,
        retval=None,
        expected_exc=OperationalError,
        num_calls=1,
    ),
    test.case(
        "sqlite_retryable",
        side_effect=Retryable,
        dialect=SupportedDialect.SQLITE,
        retval=None,
        expected_exc=OperationalError,
        num_calls=1,
    ),
)
def database_job_retry_wrapper_cases(
    side_effect: Any,
    dialect: str,
    retval: Any,
    expected_exc: type[Exception] | None,
    num_calls: int,
) -> None:
    """Test database_job_retry_wrapper."""
    instance = Mock()
    instance.db_retry_wait = 0
    instance.engine.dialect.name = dialect
    mock_job = Mock(side_effect=side_effect)

    @database_job_retry_wrapper("test", 5)
    def job(instance: Any, *args: Any, **kwargs: Any) -> Any:
        mock_job()
        return retval

    if expected_exc is None:
        expect(job(instance)).to_equal(retval)
    else:
        expect(lambda: job(instance)).to_raise(expected_exc)

    expect(len(mock_job.mock_calls)).to_equal(num_calls)


@test.cases(
    test.case(
        "mysql_ok_false",
        side_effect=None,
        dialect=SupportedDialect.MYSQL,
        retval=False,
        expected_exc=None,
    ),
    test.case(
        "mysql_ok_true",
        side_effect=None,
        dialect=SupportedDialect.MYSQL,
        retval=True,
        expected_exc=None,
    ),
    test.case(
        "mysql_valueerror",
        side_effect=ValueError,
        dialect=SupportedDialect.MYSQL,
        retval=False,
        expected_exc=ValueError,
    ),
    test.case(
        "mysql_non_retryable",
        side_effect=NonRetryable,
        dialect=SupportedDialect.MYSQL,
        retval=True,
        expected_exc=None,
    ),
    test.case(
        "mysql_retryable",
        side_effect=Retryable,
        dialect=SupportedDialect.MYSQL,
        retval=False,
        expected_exc=None,
    ),
    test.case(
        "sqlite_non_retryable",
        side_effect=NonRetryable,
        dialect=SupportedDialect.SQLITE,
        retval=True,
        expected_exc=None,
    ),
    test.case(
        "sqlite_retryable",
        side_effect=Retryable,
        dialect=SupportedDialect.SQLITE,
        retval=True,
        expected_exc=None,
    ),
)
def retryable_database_job_cases(
    side_effect: Any,
    retval: bool,
    expected_exc: type[Exception] | None,
    dialect: str,
) -> None:
    """Test retryable_database_job."""
    instance = Mock()
    instance.db_retry_wait = 0
    instance.engine.dialect.name = dialect
    mock_job = Mock(side_effect=side_effect)

    @retryable_database_job(description="test")
    def job(instance: Any, *args: Any, **kwargs: Any) -> bool:
        mock_job()
        return retval

    if expected_exc is None:
        expect(job(instance)).to_equal(retval)
    else:
        expect(lambda: job(instance)).to_raise(expected_exc)

    expect(len(mock_job.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "mysql_ok_false",
        side_effect=None,
        dialect=SupportedDialect.MYSQL,
        retval=False,
        expected_exc=None,
    ),
    test.case(
        "mysql_ok_true",
        side_effect=None,
        dialect=SupportedDialect.MYSQL,
        retval=True,
        expected_exc=None,
    ),
    test.case(
        "mysql_valueerror",
        side_effect=ValueError,
        dialect=SupportedDialect.MYSQL,
        retval=False,
        expected_exc=ValueError,
    ),
    test.case(
        "mysql_non_retryable",
        side_effect=NonRetryable,
        dialect=SupportedDialect.MYSQL,
        retval=True,
        expected_exc=None,
    ),
    test.case(
        "mysql_retryable",
        side_effect=Retryable,
        dialect=SupportedDialect.MYSQL,
        retval=False,
        expected_exc=None,
    ),
    test.case(
        "sqlite_non_retryable",
        side_effect=NonRetryable,
        dialect=SupportedDialect.SQLITE,
        retval=True,
        expected_exc=None,
    ),
    test.case(
        "sqlite_retryable",
        side_effect=Retryable,
        dialect=SupportedDialect.SQLITE,
        retval=True,
        expected_exc=None,
    ),
)
def retryable_database_job_method_cases(
    side_effect: Any,
    retval: bool,
    expected_exc: type[Exception] | None,
    dialect: str,
) -> None:
    """Test retryable_database_job_method."""
    instance = Mock()
    instance.db_retry_wait = 0
    instance.engine.dialect.name = dialect
    mock_job = Mock(side_effect=side_effect)

    class TestClass:
        @retryable_database_job_method(description="test")
        def job(self, instance: Any, *args: Any, **kwargs: Any) -> bool:
            mock_job()
            return retval

    test_obj = TestClass()
    if expected_exc is None:
        expect(test_obj.job(instance)).to_equal(retval)
    else:
        expect(lambda: test_obj.job(instance)).to_raise(expected_exc)

    expect(len(mock_job.mock_calls)).to_equal(1)


# Stubs for tests that need fixtures not yet ported (recorder_mock, caplog with
# specific patterns, issue_registry, async_setup_recorder_instance, etc.).


@test.skip("requires recorder_mock (not in tryke shim)")
async def session_scope_not_setup() -> None:
    """Stub for test_session_scope_not_setup (port deferred)."""


@test.skip("requires recorder_mock (not in tryke shim)")
async def recorder_bad_execute() -> None:
    """Stub for test_recorder_bad_execute (port deferred)."""


@test.skip("requires hass + corrupt_db_file fixture (not in tryke shim)")
async def validate_or_move_away_sqlite_database() -> None:
    """Stub for test_validate_or_move_away_sqlite_database (port deferred)."""


@test.skip("requires recorder_mock + freezer (not in tryke shim)")
async def last_run_was_recently_clean() -> None:
    """Stub for test_last_run_was_recently_clean (port deferred)."""


@test.skip("requires recorder_mock + caplog (not in tryke shim)")
async def execute_stmt_lambda_element() -> None:
    """Stub for test_execute_stmt_lambda_element (port deferred)."""


@test.skip("requires hass + freezer fixture (not in tryke shim)")
async def resolve_period() -> None:
    """Stub for test_resolve_period (port deferred)."""


@test.skip("requires hass + issue_registry (not in tryke shim)")
async def issue_for_mariadb_with_MDEV_25020() -> None:
    """Stub for test_issue_for_mariadb_with_MDEV_25020 (port deferred)."""


@test.skip("requires hass + issue_registry (not in tryke shim)")
async def no_issue_for_mariadb_with_MDEV_25020() -> None:
    """Stub for test_no_issue_for_mariadb_with_MDEV_25020 (port deferred)."""


@test.skip("requires recorder_mock + skip_by_db_engine (not in tryke shim)")
async def basic_sanity_check() -> None:
    """Stub for test_basic_sanity_check (port deferred)."""


@test.skip("requires recorder_mock + caplog + skip_by_db_engine (not in tryke shim)")
async def combined_checks() -> None:
    """Stub for test_combined_checks (port deferred)."""


@test.skip("requires recorder_mock + caplog (not in tryke shim)")
async def end_incomplete_runs() -> None:
    """Stub for test_end_incomplete_runs (port deferred)."""


@test.skip("requires recorder_mock + skip_by_db_engine (not in tryke shim)")
async def periodic_db_cleanups() -> None:
    """Stub for test_periodic_db_cleanups (port deferred)."""


@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def write_lock_db() -> None:
    """Stub for test_write_lock_db (port deferred)."""


# Keep does_not_raise available for future ports.
_ = (does_not_raise, AbstractContextManager, UTC)
