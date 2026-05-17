"""The tests for the Vacuum entity integration."""

from __future__ import annotations

from dataclasses import asdict
import logging
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.vacuum import (
    DOMAIN,
    SERVICE_CLEAN_AREA,
    SERVICE_CLEAN_SPOT,
    SERVICE_LOCATE,
    SERVICE_PAUSE,
    SERVICE_RETURN_TO_BASE,
    SERVICE_SEND_COMMAND,
    SERVICE_SET_FAN_SPEED,
    SERVICE_START,
    SERVICE_STOP,
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er, frame, issue_registry as ir

from . import (
    MockVacuum,
    MockVacuumWithCleanArea,
    help_async_setup_entry_init,
    help_async_unload_entry,
)
from ._fixtures import config_flow_fixture as config_flow_fixture_fx
from .common import async_start

from tests.common import (
    MockConfigEntry,
    MockEntity,
    MockModule,
    mock_integration,
    setup_test_component_platform,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-level anchor for tryke fixture resolution.

    Also clears the frame helper's reported-integrations cache so
    deprecation-warning tests don't share dedup state across cases.
    """
    frame._REPORTED_INTEGRATIONS.clear()
    return 0


@test.cases(
    test.case("clean_spot", service=SERVICE_CLEAN_SPOT, expected_state=VacuumActivity.CLEANING),
    test.case("pause", service=SERVICE_PAUSE, expected_state=VacuumActivity.PAUSED),
    test.case("return_to_base", service=SERVICE_RETURN_TO_BASE, expected_state=VacuumActivity.RETURNING),
    test.case("start", service=SERVICE_START, expected_state=VacuumActivity.CLEANING),
    test.case("stop", service=SERVICE_STOP, expected_state=VacuumActivity.IDLE),
)
async def state_services(
    service: str,
    expected_state: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
) -> None:
    """Test get vacuum service that affect state."""
    mock_vacuum = MockVacuum(
        name="Testing",
        entity_id="vacuum.testing",
    )
    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(hass, DOMAIN, [mock_vacuum], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    await hass.services.async_call(
        DOMAIN,
        service,
        {"entity_id": mock_vacuum.entity_id},
        blocking=True,
    )
    activity = hass.states.get(mock_vacuum.entity_id)

    expect(activity.state).to_equal(expected_state)


@test
async def fan_speed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
) -> None:
    """Test set vacuum fan speed."""
    mock_vacuum = MockVacuum(
        name="Testing",
        entity_id="vacuum.testing",
    )
    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(hass, DOMAIN, [mock_vacuum], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_FAN_SPEED,
        {"entity_id": mock_vacuum.entity_id, "fan_speed": "high"},
        blocking=True,
    )

    expect(mock_vacuum.fan_speed).to_equal("high")


@test
async def locate(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
) -> None:
    """Test vacuum locate."""

    calls: list[str] = []

    class MockVacuumWithLocation(MockVacuum):
        def __init__(self, calls: list[str], **kwargs) -> None:
            super().__init__()
            self._attr_supported_features = (
                self.supported_features | VacuumEntityFeature.LOCATE
            )
            self._calls = calls

        def locate(self, **kwargs: Any) -> None:
            self._calls.append("locate")

    mock_vacuum = MockVacuumWithLocation(
        name="Testing", entity_id="vacuum.testing", calls=calls
    )
    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(hass, DOMAIN, [mock_vacuum], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_LOCATE,
        {"entity_id": mock_vacuum.entity_id},
        blocking=True,
    )

    expect("locate" in calls).to_be(True)


@test
async def send_command(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
) -> None:
    """Test Vacuum send command."""

    strings: list[str] = []

    class MockVacuumWithSendCommand(MockVacuum):
        def __init__(self, strings: list[str], **kwargs) -> None:
            super().__init__()
            self._attr_supported_features = (
                self.supported_features | VacuumEntityFeature.SEND_COMMAND
            )
            self._strings = strings

        def send_command(
            self,
            command: str,
            params: dict[str, Any] | list[Any] | None = None,
            **kwargs: Any,
        ) -> None:
            if command == "add_str":
                self._strings.append(params["str"])

    mock_vacuum = MockVacuumWithSendCommand(
        name="Testing", entity_id="vacuum.testing", strings=strings
    )
    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(hass, DOMAIN, [mock_vacuum], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SEND_COMMAND,
        {
            "entity_id": mock_vacuum.entity_id,
            "command": "add_str",
            "params": {"str": "test"},
        },
        blocking=True,
    )

    expect("test" in strings).to_be(True)


@test.cases(
    test.case(
        "disjoint",
        area_mapping={"area_1": ["seg_1"], "area_2": ["seg_2", "seg_3"]},
        targeted_areas=["area_1", "area_2"],
        targeted_segments=["seg_1", "seg_2", "seg_3"],
    ),
    test.case(
        "overlapping",
        area_mapping={"area_1": ["seg_1", "seg_2"], "area_2": ["seg_2", "seg_3"]},
        targeted_areas=["area_1", "area_2"],
        targeted_segments=["seg_1", "seg_2", "seg_3"],
    ),
)
async def clean_area_service(
    area_mapping: dict[str, list[str]],
    targeted_areas: list[str],
    targeted_segments: list[str],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test clean_area service calls async_clean_segments with correct segments."""
    mock_vacuum = MockVacuumWithCleanArea(name="Testing", entity_id="vacuum.testing")

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(hass, DOMAIN, [mock_vacuum], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    entity_registry.async_update_entity_options(
        mock_vacuum.entity_id,
        DOMAIN,
        {
            "area_mapping": area_mapping,
            "last_seen_segments": [asdict(segment) for segment in mock_vacuum.segments],
        },
    )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLEAN_AREA,
        {"entity_id": mock_vacuum.entity_id, "cleaning_area_id": targeted_areas},
        blocking=True,
    )

    expect(len(mock_vacuum.clean_segments_calls)).to_equal(1)
    expect(mock_vacuum.clean_segments_calls[0][0]).to_equal(targeted_segments)


@test
async def clean_area_not_configured(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
) -> None:
    """Test clean_area raises when area mapping is not configured."""
    mock_vacuum = MockVacuumWithCleanArea(name="Testing", entity_id="vacuum.testing")

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(hass, DOMAIN, [mock_vacuum], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CLEAN_AREA,
            {"entity_id": mock_vacuum.entity_id, "cleaning_area_id": ["area_1"]},
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised is not None).to_be(True)
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("area_mapping_not_configured")
    expect(raised.translation_placeholders).to_equal(
        {"entity_id": mock_vacuum.entity_id}
    )


@test.cases(
    test.case(
        "empty_mapping",
        area_mapping={},
        targeted_areas=["area_2"],
        cleaned_segments=None,
    ),
    test.case(
        "missing_area",
        area_mapping={"area_1": ["seg_1"]},
        targeted_areas=["area_2"],
        cleaned_segments=None,
    ),
    test.case(
        "partial_match",
        area_mapping={"area_1": ["seg_1", "seg_2"]},
        targeted_areas=["area_1", "area_2"],
        cleaned_segments=["seg_1", "seg_2"],
    ),
)
async def clean_area_no_segments(
    area_mapping: dict[str, list[str]],
    targeted_areas: list[str],
    cleaned_segments: list[str] | None,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test clean_area raises error when areas are not mapped to vacuum segments."""
    mock_vacuum = MockVacuumWithCleanArea(name="Testing", entity_id="vacuum.testing")
    mock_vacuum_2 = MockVacuumWithCleanArea(
        name="Testing 2",
        entity_id="vacuum.testing_2",
        unique_id="mock_vacuum_2_unique_id",
    )

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(
        hass, DOMAIN, [mock_vacuum, mock_vacuum_2], from_config_entry=True
    )
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    entity_registry.async_update_entity_options(
        mock_vacuum.entity_id,
        DOMAIN,
        {
            "area_mapping": area_mapping,
            "last_seen_segments": [asdict(segment) for segment in mock_vacuum.segments],
        },
    )
    entity_registry.async_update_entity_options(
        mock_vacuum_2.entity_id,
        DOMAIN,
        {
            "area_mapping": {"area_3": ["seg_3"]},
            "last_seen_segments": [
                asdict(segment) for segment in mock_vacuum_2.segments
            ],
        },
    )

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CLEAN_AREA,
            {
                "entity_id": [mock_vacuum.entity_id, mock_vacuum_2.entity_id],
                "cleaning_area_id": [*targeted_areas, "area_3"],
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("areas_not_mapped")
    expect(raised.translation_placeholders).to_equal({"areas": "area_2"})

    if cleaned_segments is None:
        expect(len(mock_vacuum.clean_segments_calls)).to_equal(0)
    else:
        expect(len(mock_vacuum.clean_segments_calls)).to_equal(1)
        expect(mock_vacuum.clean_segments_calls[0][0]).to_equal(cleaned_segments)

    expect(len(mock_vacuum_2.clean_segments_calls)).to_equal(1)
    expect(mock_vacuum_2.clean_segments_calls[0][0]).to_equal(["seg_3"])


@test
async def clean_area_methods_not_implemented(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
) -> None:
    """Test async_get_segments and async_clean_segments raise NotImplementedError."""

    class MockVacuumNoImpl(MockEntity, StateVacuumEntity):
        """Mock vacuum without implementations."""

        _attr_supported_features = (
            VacuumEntityFeature.STATE | VacuumEntityFeature.CLEAN_AREA
        )
        _attr_activity = VacuumActivity.DOCKED

    mock_vacuum = MockVacuumNoImpl(name="Testing", entity_id="vacuum.testing")

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(hass, DOMAIN, [mock_vacuum], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    async with expect_raises_async(NotImplementedError):
        await mock_vacuum.async_get_segments()

    async with expect_raises_async(NotImplementedError):
        await mock_vacuum.async_clean_segments(["seg_1"])


@test
async def clean_area_no_registry_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test error handling when registry entry is not set."""
    mock_vacuum = MockVacuumWithCleanArea(name="Testing", entity_id="vacuum.testing")

    expect(
        lambda: mock_vacuum.last_seen_segments  # noqa: B018
    ).to_raise(RuntimeError, match="Cannot access last_seen_segments, registry entry is not set")

    call = ServiceCall(
        hass,
        DOMAIN,
        SERVICE_CLEAN_AREA,
        {"cleaning_area_id": ["area_1"]},
        context=Context(),
    )

    async with expect_raises_async(
        RuntimeError,
        match="Cannot perform area clean, registry entry is not set",
    ):
        await StateVacuumEntity.async_internal_clean_area([mock_vacuum], call)

    expect(lambda: mock_vacuum.async_create_segments_issue()).to_raise(
        RuntimeError, match="Cannot create segments issue, registry entry is not set"
    )


@test
async def last_seen_segments(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test last_seen_segments property."""
    mock_vacuum = MockVacuumWithCleanArea(name="Testing", entity_id="vacuum.testing")

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(hass, DOMAIN, [mock_vacuum], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(mock_vacuum.last_seen_segments).to_be(None)

    entity_registry.async_update_entity_options(
        mock_vacuum.entity_id,
        DOMAIN,
        {
            "area_mapping": {},
            "last_seen_segments": [asdict(segment) for segment in mock_vacuum.segments],
        },
    )

    expect(mock_vacuum.last_seen_segments).to_equal(mock_vacuum.segments)


@test
async def segments_changed_issue(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test segments changed issue."""
    mock_vacuum = MockVacuumWithCleanArea(name="Testing", entity_id="vacuum.testing")

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
    )
    setup_test_component_platform(hass, DOMAIN, [mock_vacuum], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    entity_entry = entity_registry.async_get(mock_vacuum.entity_id)

    entity_registry.async_update_entity_options(
        mock_vacuum.entity_id,
        DOMAIN,
        {
            "area_mapping": {"area_1": ["seg_1"]},
            "last_seen_segments": [asdict(segment) for segment in mock_vacuum.segments],
        },
    )
    await hass.async_block_till_done()

    mock_vacuum.async_create_segments_issue()

    issue_id = f"segments_changed_{entity_entry.id}"
    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    expect(issue is not None).to_be(True)
    expect(issue.severity).to_equal(ir.IssueSeverity.WARNING)
    expect(issue.translation_key).to_equal("segments_changed")

    entity_registry.async_update_entity_options(
        mock_vacuum.entity_id,
        DOMAIN,
        {
            "area_mapping": {"area_1": ["seg_1"], "area_2": ["seg_new"]},
            "last_seen_segments": [
                {"id": "seg_1", "name": "Kitchen"},
                {"id": "seg_new", "name": "New Room"},
            ],
        },
    )
    await hass.async_block_till_done()

    expect(ir.async_get(hass).async_get_issue(DOMAIN, issue_id)).to_be(None)


@test.cases(
    test.case("built_in", is_built_in=True, log_warnings=0),
    test.case("custom", is_built_in=False, log_warnings=3),
)
async def vacuum_log_deprecated_battery_using_properties(
    is_built_in: bool,
    log_warnings: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test incorrectly using battery properties logs warning."""

    class MockLegacyVacuum(MockVacuum):
        """Mocked vacuum entity."""

        @property
        def activity(self) -> VacuumActivity:
            """Return the state of the entity."""
            return VacuumActivity.CLEANING

        @property
        def battery_level(self) -> int:
            """Return the battery level of the vacuum."""
            return 50

        @property
        def battery_icon(self) -> str:
            """Return the battery icon of the vacuum."""
            return "mdi:battery-50"

    entity = MockLegacyVacuum(
        name="Testing",
        entity_id="vacuum.test",
    )
    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
        built_in=is_built_in,
    )
    setup_test_component_platform(hass, DOMAIN, [entity], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    state = hass.states.get(entity.entity_id)
    expect(state is not None).to_be(True)

    expect(
        len([record for record in caplog.records if record.levelno >= logging.WARNING])
    ).to_equal(log_warnings)

    expect(
        (
            "integration 'test' is setting the battery_icon which has been deprecated."
            in caplog.text
        )
        != is_built_in
    ).to_be(True)
    expect(
        (
            "integration 'test' is setting the battery_level which has been deprecated."
            in caplog.text
        )
        != is_built_in
    ).to_be(True)


@test.cases(
    test.case("built_in", is_built_in=True, log_warnings=0),
    test.case("custom", is_built_in=False, log_warnings=3),
)
async def vacuum_log_deprecated_battery_using_attr(
    is_built_in: bool,
    log_warnings: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test incorrectly using _attr_battery_* attribute does log issue and raise repair."""

    class MockLegacyVacuum(MockVacuum):
        """Mocked vacuum entity."""

        def start(self) -> None:
            """Start cleaning."""
            self._attr_battery_level = 50
            self._attr_battery_icon = "mdi:battery-50"

    entity = MockLegacyVacuum(
        name="Testing",
        entity_id="vacuum.test",
    )
    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
        built_in=is_built_in,
    )
    setup_test_component_platform(hass, DOMAIN, [entity], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    state = hass.states.get(entity.entity_id)
    expect(state is not None).to_be(True)
    entity.start()

    expect(
        len([record for record in caplog.records if record.levelno >= logging.WARNING])
    ).to_equal(log_warnings)

    expect(
        (
            "integration 'test' is setting the battery_level which has been deprecated."
            in caplog.text
        )
        != is_built_in
    ).to_be(True)
    expect(
        (
            "integration 'test' is setting the battery_icon which has been deprecated."
            in caplog.text
        )
        != is_built_in
    ).to_be(True)

    await async_start(hass, entity.entity_id)

    caplog.clear()

    await async_start(hass, entity.entity_id)

    expect(
        len([record for record in caplog.records if record.levelno >= logging.WARNING])
    ).to_equal(0)


@test.cases(
    test.case("built_in", is_built_in=True, log_warnings=0),
    test.case("custom", is_built_in=False, log_warnings=1),
)
async def vacuum_log_deprecated_battery_supported_feature(
    is_built_in: bool,
    log_warnings: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test incorrectly setting battery supported feature logs warning."""

    class MockVacuumBattery(StateVacuumEntity):
        """Mock vacuum class."""

        _attr_supported_features = (
            VacuumEntityFeature.STATE | VacuumEntityFeature.BATTERY
        )
        _attr_name = "Testing"

    entity = MockVacuumBattery()
    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=help_async_setup_entry_init,
            async_unload_entry=help_async_unload_entry,
        ),
        built_in=is_built_in,
    )
    setup_test_component_platform(hass, DOMAIN, [entity], from_config_entry=True)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    state = hass.states.get(entity.entity_id)
    expect(state is not None).to_be(True)

    expect(
        len([record for record in caplog.records if record.levelno >= logging.WARNING])
    ).to_equal(log_warnings)

    expect(
        ("integration 'test' is setting the battery supported feature" in caplog.text)
        != is_built_in
    ).to_be(True)


@test
async def vacuum_not_log_deprecated_battery_properties_during_init(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test not logging deprecation until after added to hass."""

    class MockLegacyVacuum(MockVacuum):
        """Mocked vacuum entity."""

        def __init__(self, **kwargs: Any) -> None:
            """Initialize a mock vacuum entity."""
            super().__init__(**kwargs)
            self._attr_battery_level = 50

        @property
        def activity(self) -> VacuumActivity:
            """Return the state of the entity."""
            return VacuumActivity.CLEANING

    entity = MockLegacyVacuum(
        name="Testing",
        entity_id="vacuum.test",
    )
    expect(entity.battery_level).to_equal(50)

    expect(
        len([record for record in caplog.records if record.levelno >= logging.WARNING])
    ).to_equal(0)
