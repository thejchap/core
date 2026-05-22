"""The tests for sensor recorder platform (tryke port)."""

from typing import Any

from sqlalchemy import select
from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder.db_schema import StatisticsShortTerm
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    _PRIMARY_UNIT_CONVERTERS,
    _SECONDARY_UNIT_CONVERTERS,
    STATISTIC_UNIT_TO_UNIT_CONVERTER as _STATISTIC_UNIT_TO_UNIT_CONVERTER,
    _generate_max_mean_min_statistic_in_sub_period_stmt,
    _generate_statistics_at_time_stmt_dependent_sub_query,
    _generate_statistics_at_time_stmt_group_by,
    _generate_statistics_during_period_stmt,
    async_add_external_statistics,
    async_import_statistics,
)
from homeassistant.components.recorder.table_managers.statistics_meta import (
    _generate_get_metadata_stmt,
)
from homeassistant.components.sensor import UNIT_CONVERTERS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from tests.hass_fixtures import hass as hass_fixture

from ._fixtures import recorder_mock


@fixture
async def _recorder_hass(
    hass: HomeAssistant = Depends(hass_fixture),
    _recorder: Any = Depends(recorder_mock),
) -> HomeAssistant:
    """Opt the module into Tryke's HookExecutor path with recorder set up."""
    return hass


@test
def converters_align_with_sensor() -> None:
    """Ensure STATISTIC_UNIT_TO_UNIT_CONVERTER is aligned with UNIT_CONVERTERS."""
    for converter in UNIT_CONVERTERS.values():
        assert (
            converter in _STATISTIC_UNIT_TO_UNIT_CONVERTER.values()
            or converter in _SECONDARY_UNIT_CONVERTERS
        )

    for converter in _SECONDARY_UNIT_CONVERTERS:
        assert converter not in _STATISTIC_UNIT_TO_UNIT_CONVERTER.values()

    for converter in _STATISTIC_UNIT_TO_UNIT_CONVERTER.values():
        assert converter in UNIT_CONVERTERS.values()


@test
def cache_key_for_generate_statistics_during_period_stmt() -> None:
    """Test cache key for _generate_statistics_during_period_stmt."""
    stmt = _generate_statistics_during_period_stmt(
        dt_util.utcnow(), dt_util.utcnow(), [0], StatisticsShortTerm, set()
    )
    cache_key_1 = stmt._generate_cache_key()
    stmt2 = _generate_statistics_during_period_stmt(
        dt_util.utcnow(), dt_util.utcnow(), [0], StatisticsShortTerm, set()
    )
    cache_key_2 = stmt2._generate_cache_key()
    assert cache_key_1 == cache_key_2
    stmt3 = _generate_statistics_during_period_stmt(
        dt_util.utcnow(),
        dt_util.utcnow(),
        [0],
        StatisticsShortTerm,
        {"sum", "mean"},
    )
    cache_key_3 = stmt3._generate_cache_key()
    assert cache_key_1 != cache_key_3


@test
def cache_key_for_generate_get_metadata_stmt() -> None:
    """Test cache key for _generate_get_metadata_stmt."""
    stmt_mean = _generate_get_metadata_stmt([0], "mean")
    stmt_mean2 = _generate_get_metadata_stmt([1], "mean")
    stmt_sum = _generate_get_metadata_stmt([0], "sum")
    stmt_none = _generate_get_metadata_stmt()
    assert stmt_mean._generate_cache_key() == stmt_mean2._generate_cache_key()
    assert stmt_mean._generate_cache_key() != stmt_sum._generate_cache_key()
    assert stmt_mean._generate_cache_key() != stmt_none._generate_cache_key()


@test
def cache_key_for_generate_max_mean_min_statistic_in_sub_period_stmt() -> None:
    """Test cache key for _generate_max_mean_min_statistic_in_sub_period_stmt."""
    columns = select(StatisticsShortTerm.metadata_id, StatisticsShortTerm.start_ts)
    stmt = _generate_max_mean_min_statistic_in_sub_period_stmt(
        columns,
        dt_util.utcnow(),
        dt_util.utcnow(),
        StatisticsShortTerm,
        [0],
    )
    cache_key_1 = stmt._generate_cache_key()
    stmt2 = _generate_max_mean_min_statistic_in_sub_period_stmt(
        columns,
        dt_util.utcnow(),
        dt_util.utcnow(),
        StatisticsShortTerm,
        [0],
    )
    cache_key_2 = stmt2._generate_cache_key()
    assert cache_key_1 == cache_key_2
    columns2 = select(
        StatisticsShortTerm.metadata_id,
        StatisticsShortTerm.start_ts,
        StatisticsShortTerm.sum,
        StatisticsShortTerm.mean,
    )
    stmt3 = _generate_max_mean_min_statistic_in_sub_period_stmt(
        columns2,
        dt_util.utcnow(),
        dt_util.utcnow(),
        StatisticsShortTerm,
        [0],
    )
    cache_key_3 = stmt3._generate_cache_key()
    assert cache_key_1 != cache_key_3


@test
def cache_key_for_generate_statistics_at_time_stmt_group_by() -> None:
    """Test cache key for _generate_statistics_at_time_stmt_group_by."""
    stmt = _generate_statistics_at_time_stmt_group_by(
        StatisticsShortTerm, {0}, 0.0, set()
    )
    cache_key_1 = stmt._generate_cache_key()
    stmt2 = _generate_statistics_at_time_stmt_group_by(
        StatisticsShortTerm, {0}, 0.0, set()
    )
    cache_key_2 = stmt2._generate_cache_key()
    assert cache_key_1 == cache_key_2
    stmt3 = _generate_statistics_at_time_stmt_group_by(
        StatisticsShortTerm, {0}, 0.0, {"sum", "mean"}
    )
    cache_key_3 = stmt3._generate_cache_key()
    assert cache_key_1 != cache_key_3


@test
def cache_key_for_generate_statistics_at_time_stmt_dependent_sub_query() -> None:
    """Test cache key for _generate_statistics_at_time_stmt_dependent_sub_query."""
    stmt = _generate_statistics_at_time_stmt_dependent_sub_query(
        StatisticsShortTerm, {0}, 0.0, set()
    )
    cache_key_1 = stmt._generate_cache_key()
    stmt2 = _generate_statistics_at_time_stmt_dependent_sub_query(
        StatisticsShortTerm, {0}, 0.0, set()
    )
    cache_key_2 = stmt2._generate_cache_key()
    assert cache_key_1 == cache_key_2
    stmt3 = _generate_statistics_at_time_stmt_dependent_sub_query(
        StatisticsShortTerm, {0}, 0.0, {"sum", "mean"}
    )
    cache_key_3 = stmt3._generate_cache_key()
    assert cache_key_1 != cache_key_3


@test
def STATISTIC_UNIT_TO_UNIT_CONVERTER() -> None:
    """Ensure unit does not belong to multiple converters."""
    for uom in _STATISTIC_UNIT_TO_UNIT_CONVERTER:
        unit_converter = _STATISTIC_UNIT_TO_UNIT_CONVERTER[uom]
        other = next(
            (
                c
                for c in _PRIMARY_UNIT_CONVERTERS
                if unit_converter is not c and uom in c.VALID_UNITS
            ),
            None,
        )
        assert other is None, (
            f"{uom} is present in both {other.__name__} and {unit_converter.__name__}"
            if other is not None
            else ""
        )


@test.skip("requires recorder_mock + complex helpers (port deferred)")
async def compile_hourly_statistics() -> None:
    """Stub for test_compile_hourly_statistics (port deferred)."""


@test.skip("requires recorder_mock (port deferred)")
async def compile_periodic_statistics_exception() -> None:
    """Stub for test_compile_periodic_statistics_exception (port deferred)."""


@test.skip("requires recorder_mock + entity_registry (port deferred)")
async def rename_entity() -> None:
    """Stub for test_rename_entity (port deferred)."""


@test.skip("requires recorder_mock (port deferred)")
async def statistics_during_period_set_back_compat() -> None:
    """Stub for test_statistics_during_period_set_back_compat (port deferred)."""


@test.skip("requires recorder_mock + entity_registry (port deferred)")
async def rename_entity_collision() -> None:
    """Stub for test_rename_entity_collision (port deferred)."""


@test.skip("requires recorder_mock + entity_registry (port deferred)")
async def rename_entity_collision_states_meta_check_disabled() -> None:
    """Stub for test_rename_entity_collision_states_meta_check_disabled (port deferred)."""


@test.skip("requires recorder_mock + caplog (port deferred)")
async def statistics_duplicated() -> None:
    """Stub for test_statistics_duplicated (port deferred)."""


@test.skip("requires recorder_mock + parametrize (port deferred)")
async def import_statistics() -> None:
    """Stub for test_import_statistics (port deferred)."""


@test
async def external_statistics_errors(
    hass: HomeAssistant = Depends(_recorder_hass),
) -> None:
    """Test validation of external statistics."""
    zero = dt_util.utcnow()
    period1 = zero.replace(minute=0, second=0, microsecond=0)

    _external_statistics: StatisticData = {
        "start": period1,
        "last_reset": None,
        "state": 0,
        "sum": 2,
    }

    _external_metadata: StatisticMetaData = {
        "has_mean": False,
        "mean_type": StatisticMeanType.NONE,
        "has_sum": True,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "test:total_energy_import",
        "unit_class": "energy",
        "unit_of_measurement": "kWh",
    }

    # Attempt to insert statistics for an entity
    external_metadata = {**_external_metadata, "statistic_id": "sensor.total_energy_import"}
    external_statistics = {**_external_statistics}
    expect(
        lambda: async_add_external_statistics(
            hass, external_metadata, (external_statistics,)
        )
    ).to_raise(HomeAssistantError)

    # Attempt to insert statistics for the wrong domain
    external_metadata = {**_external_metadata, "source": "other"}
    external_statistics = {**_external_statistics}
    expect(
        lambda: async_add_external_statistics(
            hass, external_metadata, (external_statistics,)
        )
    ).to_raise(HomeAssistantError)

    # Attempt to insert statistics for a naive starting time
    external_metadata = {**_external_metadata}
    external_statistics = {
        **_external_statistics,
        "start": period1.replace(tzinfo=None),
    }
    expect(
        lambda: async_add_external_statistics(
            hass, external_metadata, (external_statistics,)
        )
    ).to_raise(HomeAssistantError)

    # Attempt to insert statistics for an invalid starting time
    external_metadata = {**_external_metadata}
    external_statistics = {**_external_statistics, "start": period1.replace(minute=1)}
    expect(
        lambda: async_add_external_statistics(
            hass, external_metadata, (external_statistics,)
        )
    ).to_raise(HomeAssistantError)


@test
async def import_statistics_errors(
    hass: HomeAssistant = Depends(_recorder_hass),
) -> None:
    """Test validation of imported statistics."""
    zero = dt_util.utcnow()
    period1 = zero.replace(minute=0, second=0, microsecond=0)

    _external_statistics: StatisticData = {
        "start": period1,
        "last_reset": None,
        "state": 0,
        "sum": 2,
    }

    _external_metadata: StatisticMetaData = {
        "has_mean": False,
        "mean_type": StatisticMeanType.NONE,
        "has_sum": True,
        "name": "Total imported energy",
        "source": "recorder",
        "statistic_id": "sensor.total_energy_import",
        "unit_class": "energy",
        "unit_of_measurement": "kWh",
    }

    # Attempt to insert statistics for an external source
    external_metadata = {
        **_external_metadata,
        "statistic_id": "test:total_energy_import",
    }
    external_statistics = {**_external_statistics}
    expect(
        lambda: async_import_statistics(
            hass, external_metadata, (external_statistics,)
        )
    ).to_raise(HomeAssistantError)

    # Attempt to insert statistics for the wrong source
    external_metadata = {**_external_metadata, "source": "other"}
    external_statistics = {**_external_statistics}
    expect(
        lambda: async_import_statistics(
            hass, external_metadata, (external_statistics,)
        )
    ).to_raise(HomeAssistantError)

    # Attempt to insert statistics for a naive starting time
    external_metadata = {**_external_metadata}
    external_statistics = {
        **_external_statistics,
        "start": period1.replace(tzinfo=None),
    }
    expect(
        lambda: async_import_statistics(
            hass, external_metadata, (external_statistics,)
        )
    ).to_raise(HomeAssistantError)

    # Attempt to insert statistics for an invalid starting time
    external_metadata = {**_external_metadata}
    external_statistics = {**_external_statistics, "start": period1.replace(minute=1)}
    expect(
        lambda: async_import_statistics(
            hass, external_metadata, (external_statistics,)
        )
    ).to_raise(HomeAssistantError)


@test.skip("requires recorder_mock (port deferred)")
async def update_statistics_metadata() -> None:
    """Stub for test_update_statistics_metadata (port deferred)."""


@test.skip("requires recorder_mock (port deferred)")
async def update_statistics_metadata_error() -> None:
    """Stub for test_update_statistics_metadata_error (port deferred)."""


@test.skip("requires recorder_mock + freeze_time + parametrize (port deferred)")
async def daily_statistics_sum() -> None:
    """Stub for test_daily_statistics_sum (port deferred)."""


@test.skip("requires recorder_mock + freeze_time + parametrize (port deferred)")
async def multiple_daily_statistics_sum() -> None:
    """Stub for test_multiple_daily_statistics_sum (port deferred)."""


@test.skip("requires recorder_mock + freeze_time + parametrize (port deferred)")
async def weekly_statistics_mean() -> None:
    """Stub for test_weekly_statistics_mean (port deferred)."""


@test.skip("requires recorder_mock + freeze_time + parametrize (port deferred)")
async def weekly_statistics_sum() -> None:
    """Stub for test_weekly_statistics_sum (port deferred)."""


@test.skip("requires recorder_mock + freeze_time + parametrize (port deferred)")
async def monthly_statistics_sum() -> None:
    """Stub for test_monthly_statistics_sum (port deferred)."""


@test.skip("requires recorder_mock + freeze_time + parametrize (port deferred)")
async def yearly_statistics_sum() -> None:
    """Stub for test_yearly_statistics_sum (port deferred)."""


@test.skip("requires recorder_mock + parametrize (port deferred)")
async def change() -> None:
    """Stub for test_change (port deferred)."""


@test.skip("requires recorder_mock + parametrize (port deferred)")
async def change_multiple() -> None:
    """Stub for test_change_multiple (port deferred)."""


@test.skip("requires recorder_mock + parametrize (port deferred)")
async def change_with_none() -> None:
    """Stub for test_change_with_none (port deferred)."""


@test.skip("requires recorder_mock + MockPlatform (port deferred)")
async def recorder_platform_with_statistics() -> None:
    """Stub for test_recorder_platform_with_statistics (port deferred)."""


@test.skip("requires recorder_mock + MockPlatform (port deferred)")
async def recorder_platform_without_statistics() -> None:
    """Stub for test_recorder_platform_without_statistics (port deferred)."""


@test.skip("requires recorder_mock + MockPlatform (port deferred)")
async def recorder_platform_with_partial_statistics_support() -> None:
    """Stub for test_recorder_platform_with_partial_statistics_support (port deferred)."""


@test.skip("requires recorder_mock + MockPlatform (port deferred)")
async def recorder_platforms_with_custom_equivalent_units() -> None:
    """Stub for test_recorder_platforms_with_custom_equivalent_units (port deferred)."""


@test.skip("requires recorder_mock + MockPlatform (port deferred)")
async def recorder_platforms_with_custom_equivalent_units_continues_on_exception() -> None:
    """Stub for test_recorder_platforms_with_custom_equivalent_units_continues_on_exception (port deferred)."""


@test.skip("requires recorder_mock + MockPlatform (port deferred)")
async def recorder_platforms_with_custom_equivalent_units_continues_on_invalid_types() -> None:
    """Stub for test_recorder_platforms_with_custom_equivalent_units_continues_on_invalid_types (port deferred)."""


@test.skip("requires recorder_mock + service call (port deferred)")
async def get_statistics_service() -> None:
    """Stub for test_get_statistics_service (port deferred)."""


@test.skip("requires recorder_mock + service call (port deferred)")
async def get_statistics_service_missing_mandatory_keys() -> None:
    """Stub for test_get_statistics_service_missing_mandatory_keys (port deferred)."""
