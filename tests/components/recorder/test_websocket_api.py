"""The tests for the recorder websocket API (tryke port)."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder.websocket_api import UNIT_SCHEMA
from homeassistant.components.sensor import UNIT_CONVERTERS
from homeassistant.core import HomeAssistant

from ._fixtures import recorder_mock
from .common import async_wait_recording_done

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.typing import WebSocketGenerator


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Anchor fixture for tryke Depends() resolution."""
    return 0


@fixture
async def _recorder_executor(
    _network: None = Depends(mock_network),
    _recorder: Any = Depends(recorder_mock),
) -> int:
    """Anchor fixture for tests needing the recorder."""
    return 0


@test
async def converters_align_with_sensor(
    _trigger: int = Depends(_trigger_executor),
) -> None:
    """Ensure UNIT_SCHEMA is aligned with sensor UNIT_CONVERTERS."""
    for converter in UNIT_CONVERTERS.values():
        expect(converter.UNIT_CLASS in UNIT_SCHEMA.schema).to_be(True)

    for unit_class in UNIT_SCHEMA.schema:
        expect(
            any(c for c in UNIT_CONVERTERS.values() if unit_class == c.UNIT_CLASS)
        ).to_be(True)


@test
async def recorder_info(
    _recorder: int = Depends(_recorder_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting recorder status."""
    client = await hass_ws_client(hass)

    # Ensure there are no queued events
    await async_wait_recording_done(hass)

    await client.send_json_auto_id({"type": "recorder/info"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(
        {
            "backlog": 0,
            "db_in_default_location": False,
            "max_backlog": 65000,
            "migration_in_progress": False,
            "migration_is_live": False,
            "recording": True,
            "thread_running": True,
        }
    )


@test.skip("requires fresh hass without recorder pre-loaded by shared fixture")
async def recorder_info_no_recorder() -> None:
    """Stub for test_recorder_info_no_recorder (port deferred)."""


# Stubs for tests that need fixtures not yet ported (freezer, instrument_migration,
# async_test_recorder, recorder_mock with custom config, parametrize, etc.).

@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistics_during_period() -> None:
    """Stub for test_statistics_during_period (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistic_during_period() -> None:
    """Stub for test_statistic_during_period (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistic_during_period_circular_mean() -> None:
    """Stub for test_statistic_during_period_circular_mean (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistic_during_period_hole() -> None:
    """Stub for test_statistic_during_period_hole (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistic_during_period_hole_circular_mean() -> None:
    """Stub for test_statistic_during_period_hole_circular_mean (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistic_during_period_partial_overlap() -> None:
    """Stub for test_statistic_during_period_partial_overlap (port deferred)."""


@test.skip("requires freezer fixture (not in tryke shim)")
async def statistic_during_period_calendar() -> None:
    """Stub for test_statistic_during_period_calendar (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistics_during_period_unit_conversion() -> None:
    """Stub for test_statistics_during_period_unit_conversion (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def sum_statistics_during_period_unit_conversion() -> None:
    """Stub for test_sum_statistics_during_period_unit_conversion (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistics_during_period_invalid_unit_conversion() -> None:
    """Stub for test_statistics_during_period_invalid_unit_conversion (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistics_during_period_in_the_past() -> None:
    """Stub for test_statistics_during_period_in_the_past (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistics_during_period_bad_start_time() -> None:
    """Stub for test_statistics_during_period_bad_start_time (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistics_during_period_bad_end_time() -> None:
    """Stub for test_statistics_during_period_bad_end_time (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistics_during_period_no_statistic_ids() -> None:
    """Stub for test_statistics_during_period_no_statistic_ids (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def statistics_during_period_empty_statistic_ids() -> None:
    """Stub for test_statistics_during_period_empty_statistic_ids (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def list_statistic_ids() -> None:
    """Stub for test_list_statistic_ids (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def list_statistic_ids_unit_change() -> None:
    """Stub for test_list_statistic_ids_unit_change (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def validate_statistics() -> None:
    """Stub for test_validate_statistics (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def update_statistics_issues() -> None:
    """Stub for test_update_statistics_issues (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def clear_statistics() -> None:
    """Stub for test_clear_statistics (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def clear_statistics_time_out() -> None:
    """Stub for test_clear_statistics_time_out (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def update_statistics_metadata() -> None:
    """Stub for test_update_statistics_metadata (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def update_statistics_metadata_error() -> None:
    """Stub for test_update_statistics_metadata_error (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def update_statistics_metadata_time_out() -> None:
    """Stub for test_update_statistics_metadata_time_out (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def change_statistics_unit() -> None:
    """Stub for test_change_statistics_unit (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def change_statistics_unit_errors() -> None:
    """Stub for test_change_statistics_unit_errors (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def recorder_info_default_url() -> None:
    """Stub for test_recorder_info_default_url (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def recorder_info_bad_recorder_config() -> None:
    """Stub for test_recorder_info_bad_recorder_config (port deferred)."""


@test.skip("requires async_test_recorder (not in tryke shim)")
async def recorder_info_wait_database_connect() -> None:
    """Stub for test_recorder_info_wait_database_connect (port deferred)."""


@test.skip("requires instrument_migration (not in tryke shim)")
async def recorder_info_migration_queue_exhausted() -> None:
    """Stub for test_recorder_info_migration_queue_exhausted (port deferred)."""


@test.skip("requires hass_supervisor_access_token (not in tryke shim)")
async def backup_start_no_recorder() -> None:
    """Stub for test_backup_start_no_recorder (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def get_statistics_metadata() -> None:
    """Stub for test_get_statistics_metadata (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def import_statistics() -> None:
    """Stub for test_import_statistics (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def import_statistics_with_error() -> None:
    """Stub for test_import_statistics_with_error (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def adjust_sum_statistics_energy() -> None:
    """Stub for test_adjust_sum_statistics_energy (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def adjust_sum_statistics_gas() -> None:
    """Stub for test_adjust_sum_statistics_gas (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def adjust_sum_statistics_errors() -> None:
    """Stub for test_adjust_sum_statistics_errors (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def import_statistics_with_last_reset() -> None:
    """Stub for test_import_statistics_with_last_reset (port deferred)."""
