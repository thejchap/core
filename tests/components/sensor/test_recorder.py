"""The tests for sensor recorder platform (tryke port)."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder.db_schema import (
    StateAttributes,
    States,
    StatesMeta,
)
from homeassistant.components.recorder.util import session_scope
from homeassistant.components.sensor import (
    ATTR_OPTIONS,
    DOMAIN,
    SensorDeviceClass,
)
from homeassistant.components.sensor.recorder import (
    MEAN_TYPE_CHANGED_ISSUE,
    STATE_CLASS_REMOVED_ISSUE,
    UNITS_CHANGED_ISSUE,
)
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from .common import MockSensor
from ._fixtures import recorder_mock

from tests.common import setup_test_component_platform
from tests.components.recorder.common import (
    async_wait_recording_done,
    db_state_attributes_to_native,
    db_state_to_native,
)
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
) -> int:
    """Force tryke fixture resolution before each test."""
    return 0


@test
async def exclude_attributes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sensor attributes to be excluded."""
    entity0 = MockSensor(
        has_entity_name=True,
        unique_id="test",
        name="Test",
        native_value="option1",
        device_class=SensorDeviceClass.ENUM,
        options=["option1", "option2"],
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])
    expect(
        await async_setup_component(hass, "sensor", {"sensor": {"platform": "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    def _fetch_states() -> list[State]:
        with session_scope(hass=hass, read_only=True) as session:
            native_states = []
            for db_state, db_state_attributes, db_states_meta in (
                session.query(States, StateAttributes, StatesMeta)
                .outerjoin(
                    StateAttributes,
                    States.attributes_id == StateAttributes.attributes_id,
                )
                .outerjoin(StatesMeta, States.metadata_id == StatesMeta.metadata_id)
            ):
                db_state.entity_id = db_states_meta.entity_id
                state = db_state_to_native(db_state)
                state.attributes = db_state_attributes_to_native(db_state_attributes)
                native_states.append(state)
            return native_states

    states: list[State] = await hass.async_add_executor_job(_fetch_states)
    expect(len(states)).to_equal(1)
    expect(ATTR_OPTIONS in states[0].attributes).to_be_falsy()
    expect(ATTR_FRIENDLY_NAME in states[0].attributes).to_be_truthy()


@test
async def clean_up_repairs(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
) -> None:
    """Test cleaning up repairs."""
    await async_setup_component(hass, "sensor", {})
    issue_registry = ir.async_get(hass)
    client = await hass_ws_client()

    def create_issue(domain: str, issue_id: str, data: dict | None) -> None:
        ir.async_create_issue(
            hass,
            domain,
            issue_id,
            data=data,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="",
        )

    create_issue("test", "test_issue", None)
    create_issue(DOMAIN, "test_issue_1", None)
    create_issue(DOMAIN, "test_issue_2", {"issue_type": "another_issue"})
    create_issue(DOMAIN, "test_issue_3", {"issue_type": STATE_CLASS_REMOVED_ISSUE})
    create_issue(DOMAIN, "test_issue_4", {"issue_type": UNITS_CHANGED_ISSUE})
    create_issue(DOMAIN, "test_issue_5", {"issue_type": MEAN_TYPE_CHANGED_ISSUE})

    expect(set(issue_registry.issues)).to_equal(
        {
            ("test", "test_issue"),
            ("sensor", "test_issue_1"),
            ("sensor", "test_issue_2"),
            ("sensor", "test_issue_3"),
            ("sensor", "test_issue_4"),
            ("sensor", "test_issue_5"),
        }
    )

    await client.send_json_auto_id({"type": "recorder/update_statistics_issues"})
    response = await client.receive_json()
    expect(response["success"]).to_be_truthy()

    expect(set(issue_registry.issues)).to_equal(
        {
            ("test", "test_issue"),
            ("sensor", "test_issue_1"),
            ("sensor", "test_issue_2"),
        }
    )


# The remaining tests in the upstream pytest file are deeply tied to fixtures
# (freezegun, recorder statistics helpers, parametrize matrices, custom
# helpers like assert_validation_result/async_recorder_block_till_done) that
# have not been wired into the tryke shim yet; they remain stubbed.


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics() -> None:
    """Stub for test_compile_hourly_statistics (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_angle() -> None:
    """Stub for test_compile_hourly_statistics_angle (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_with_some_same_last_updated() -> None:
    """Stub for test_compile_hourly_statistics_with_some_same_last_updated."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_with_some_same_last_updated_angle() -> None:
    """Stub for test_compile_hourly_statistics_with_some_same_last_updated_angle."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_with_all_same_last_updated() -> None:
    """Stub for test_compile_hourly_statistics_with_all_same_last_updated."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_only_state_is_at_end_of_period() -> None:
    """Stub for test_compile_hourly_statistics_only_state_is_at_end_of_period."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_purged_state_changes() -> None:
    """Stub for test_compile_hourly_statistics_purged_state_changes."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_ignore_future_state() -> None:
    """Stub for test_compile_hourly_statistics_ignore_future_state."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_wrong_unit() -> None:
    """Stub for test_compile_hourly_statistics_wrong_unit (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_sum_statistics_amount() -> None:
    """Stub for test_compile_hourly_sum_statistics_amount (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_sum_statistics_amount_reset_every_state_change() -> None:
    """Stub for test_compile_hourly_sum_statistics_amount_reset_every_state_change."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_sum_statistics_amount_invalid_last_reset() -> None:
    """Stub for test_compile_hourly_sum_statistics_amount_invalid_last_reset."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_sum_statistics_nan_inf_state() -> None:
    """Stub for test_compile_hourly_sum_statistics_nan_inf_state."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_sum_statistics_negative_state() -> None:
    """Stub for test_compile_hourly_sum_statistics_negative_state."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_sum_statistics_total_no_reset() -> None:
    """Stub for test_compile_hourly_sum_statistics_total_no_reset."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_sum_statistics_total_increasing() -> None:
    """Stub for test_compile_hourly_sum_statistics_total_increasing."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_sum_statistics_total_increasing_small_dip() -> None:
    """Stub for test_compile_hourly_sum_statistics_total_increasing_small_dip."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_energy_statistics_unsupported() -> None:
    """Stub for test_compile_hourly_energy_statistics_unsupported."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_energy_statistics_multiple() -> None:
    """Stub for test_compile_hourly_energy_statistics_multiple."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_unchanged() -> None:
    """Stub for test_compile_hourly_statistics_unchanged."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_unchanged_angle() -> None:
    """Stub for test_compile_hourly_statistics_unchanged_angle."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_partially_unavailable() -> None:
    """Stub for test_compile_hourly_statistics_partially_unavailable."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_unavailable() -> None:
    """Stub for test_compile_hourly_statistics_unavailable."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_unavailable_angle() -> None:
    """Stub for test_compile_hourly_statistics_unavailable_angle."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_fails() -> None:
    """Stub for test_compile_hourly_statistics_fails (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def list_statistic_ids() -> None:
    """Stub for test_list_statistic_ids (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def list_statistic_ids_unsupported() -> None:
    """Stub for test_list_statistic_ids_unsupported (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_changing_units_1() -> None:
    """Stub for test_compile_hourly_statistics_changing_units_1."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_changing_units_2() -> None:
    """Stub for test_compile_hourly_statistics_changing_units_2."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_changing_units_3() -> None:
    """Stub for test_compile_hourly_statistics_changing_units_3."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_convert_units_1() -> None:
    """Stub for test_compile_hourly_statistics_convert_units_1."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_equivalent_units_1() -> None:
    """Stub for test_compile_hourly_statistics_equivalent_units_1."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_equivalent_units_2() -> None:
    """Stub for test_compile_hourly_statistics_equivalent_units_2."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_custom_equivalent_units() -> None:
    """Stub for test_compile_hourly_statistics_custom_equivalent_units."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_changing_device_class_1() -> None:
    """Stub for test_compile_hourly_statistics_changing_device_class_1."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_changing_device_class_2() -> None:
    """Stub for test_compile_hourly_statistics_changing_device_class_2."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_hourly_statistics_changing_state_class() -> None:
    """Stub for test_compile_hourly_statistics_changing_state_class."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def compile_statistics_hourly_daily_monthly_summary() -> None:
    """Stub for test_compile_statistics_hourly_daily_monthly_summary."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_unit_change_convertible() -> None:
    """Stub for test_validate_unit_change_convertible (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_unit_ignore_device_class() -> None:
    """Stub for test_validate_statistics_unit_ignore_device_class."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_unit_change_no_device_class() -> None:
    """Stub for test_validate_statistics_unit_change_no_device_class."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_state_class_removed() -> None:
    """Stub for test_validate_statistics_state_class_removed."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_state_class_removed_issue_cleaned_up() -> None:
    """Stub for test_validate_statistics_state_class_removed_issue_cleaned_up."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_sensor_no_longer_recorded() -> None:
    """Stub for test_validate_statistics_sensor_no_longer_recorded."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_sensor_not_recorded() -> None:
    """Stub for test_validate_statistics_sensor_not_recorded."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_sensor_removed() -> None:
    """Stub for test_validate_statistics_sensor_removed."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_unit_change_no_conversion() -> None:
    """Stub for test_validate_statistics_unit_change_no_conversion."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_unit_change_equivalent_units() -> None:
    """Stub for test_validate_statistics_unit_change_equivalent_units."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_unit_change_equivalent_units_2() -> None:
    """Stub for test_validate_statistics_unit_change_equivalent_units_2."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_unit_change_custom_equivalent_units() -> None:
    """Stub for test_validate_statistics_unit_change_custom_equivalent_units."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_other_domain() -> None:
    """Stub for test_validate_statistics_other_domain (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def update_statistics_issues() -> None:
    """Stub for test_update_statistics_issues (port deferred)."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def update_statistics_issues_with_custom_equivalent_units() -> None:
    """Stub for test_update_statistics_issues_with_custom_equivalent_units."""


@test.skip("port deferred: heavy parametrize + freezegun + statistics helpers")
async def validate_statistics_mean_type_changed() -> None:
    """Stub for test_validate_statistics_mean_type_changed (port deferred)."""
