"""The tests for the native services of Evohome."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.evohome.climate import EvoZone
from homeassistant.components.evohome.const import (
    ATTR_DURATION,
    ATTR_PERIOD,
    ATTR_SETPOINT,
    DOMAIN,
    RESET_BREAKS_IN_HA_VERSION,
    SERVICE_BREAKS_IN_HA_VERSION,
    EvoService,
)
from homeassistant.components.evohome.water_heater import EvoDHW
from homeassistant.components.water_heater import DOMAIN as WATER_HEATER_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, ATTR_MODE, ATTR_STATE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.entity_platform import DATA_DOMAIN_PLATFORM_ENTITIES

from ._fixtures import setup_evo_for_test

from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    freezer as freezer_fx,
    hass as hass_fx,
    issue_registry as issue_registry_fx,
    mock_network as mock_network_fx,
)
@fixture
def _trigger_executor() -> int:
    """Force tryke to run tests through the async executor."""
    return 0


@test
async def refresh_system(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test Evohome's refresh_system service (for all temperature control systems)."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry):
        # EvoService.REFRESH_SYSTEM
        with patch("evohomeasync2.location.Location.update") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.REFRESH_SYSTEM,
                {},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with()


@test.cases(
    test.case("minimal", install="minimal"),
    test.case("default", install="default"),
    test.case("h032585", install="h032585"),
    test.case("h099625", install="h099625"),
    test.case("h139906", install="h139906"),
    test.case("h157546", install="h157546"),
    test.case("sys_004", install="sys_004"),
)
async def reset_system(
    install: str,
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test untargeted reset_system service calls."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, install, entity_registry):
        # EvoService.RESET_SYSTEM
        with patch("evohomeasync2.control_system.ControlSystem.reset") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.RESET_SYSTEM,
                {},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with()

        issue = issue_registry.async_get_issue(
            DOMAIN, "deprecated_reset_system_service"
        )
        expect(issue).not_.to_be_none()
        expect(issue.translation_key).to_equal("deprecated_reset_system_service")
        expect(issue.translation_placeholders).to_equal(
            {"breaks_in_ha_version": RESET_BREAKS_IN_HA_VERSION}
        )


@test
async def set_system_mode_deprecated(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test untargeted set_system_mode service calls.

    These untargeted service calls remain supported during the deprecation
    window but should cause a Repair issue.
    """
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry):
        # EvoService.SET_SYSTEM_MODE: Auto
        with patch(
            "evohomeasync2.control_system.ControlSystem.set_mode"
        ) as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_SYSTEM_MODE,
                {ATTR_MODE: "Auto"},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with("Auto", until=None)

        issue = issue_registry.async_get_issue(
            DOMAIN, "deprecated_set_system_mode_service"
        )
        expect(issue).not_.to_be_none()
        expect(issue.translation_key).to_equal("deprecated_controller_service")
        expect(issue.translation_placeholders).to_equal(
            {
                "breaks_in_ha_version": SERVICE_BREAKS_IN_HA_VERSION,
                "service": EvoService.SET_SYSTEM_MODE,
            }
        )

        freezer.move_to("2024-07-10T12:00:00+00:00")

        # EvoService.SET_SYSTEM_MODE: AutoWithEco, hours=12
        with patch(
            "evohomeasync2.control_system.ControlSystem.set_mode"
        ) as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_SYSTEM_MODE,
                {ATTR_MODE: "AutoWithEco", ATTR_DURATION: {"hours": 12}},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(
                "AutoWithEco", until=datetime(2024, 7, 11, 0, 0, tzinfo=UTC)
            )

        # EvoService.SET_SYSTEM_MODE: Away, days=7
        with patch(
            "evohomeasync2.control_system.ControlSystem.set_mode"
        ) as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_SYSTEM_MODE,
                {ATTR_MODE: "Away", ATTR_PERIOD: {"days": 7}},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(
                "Away", until=datetime(2024, 7, 16, 23, 0, tzinfo=UTC)
            )


@test
async def set_system_mode(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test entity-targeted set_system_mode service calls."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        ctl_id = evo.ctl_id

        freezer.move_to("2024-07-10T12:00:00+00:00")

        with patch(
            "evohomeasync2.control_system.ControlSystem.set_mode"
        ) as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_SYSTEM_MODE,
                {ATTR_MODE: "Away", ATTR_PERIOD: {"days": 7}},
                target={ATTR_ENTITY_ID: ctl_id},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(
                "Away", until=datetime(2024, 7, 16, 23, 0, tzinfo=UTC)
            )

        # can remove, once the domain-level service is removed
        with patch(
            "evohomeasync2.control_system.ControlSystem.set_mode"
        ) as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_SYSTEM_MODE,
                {
                    ATTR_ENTITY_ID: ctl_id,
                    ATTR_MODE: "Away",
                    ATTR_PERIOD: {"days": 7},
                },
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(
                "Away", until=datetime(2024, 7, 16, 23, 0, tzinfo=UTC)
            )

        issue = issue_registry.async_get_issue(
            DOMAIN, "deprecated_set_system_mode_service"
        )
        expect(issue).to_be_none()


@test
async def clear_zone_override(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test Evohome's clear_zone_override service (for a heating zone)."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        zone_id = evo.zone_id

        # EvoZoneMode.FOLLOW_SCHEDULE
        with patch("evohomeasync2.zone.Zone.reset") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.CLEAR_ZONE_OVERRIDE,
                {},
                target={ATTR_ENTITY_ID: zone_id},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with()

        issue = issue_registry.async_get_issue(
            DOMAIN, "deprecated_clear_zone_override_service"
        )
        expect(issue).not_.to_be_none()
        expect(issue.translation_key).to_equal(
            "deprecated_clear_zone_override_service"
        )
        expect(issue.translation_placeholders).to_equal(
            {"breaks_in_ha_version": RESET_BREAKS_IN_HA_VERSION}
        )


@test
async def clear_zone_override_legacy(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test Evohome's clear_zone_override service with the legacy entity_id."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        zone_id = evo.zone_id

        # EvoZoneMode.FOLLOW_SCHEDULE
        with patch("evohomeasync2.zone.Zone.reset") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.CLEAR_ZONE_OVERRIDE,
                {ATTR_ENTITY_ID: zone_id},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with()

        issue = issue_registry.async_get_issue(
            DOMAIN, "deprecated_clear_zone_override_service"
        )
        expect(issue).not_.to_be_none()
        expect(issue.translation_key).to_equal(
            "deprecated_clear_zone_override_service"
        )
        expect(issue.translation_placeholders).to_equal(
            {"breaks_in_ha_version": RESET_BREAKS_IN_HA_VERSION}
        )


@test
async def set_zone_override(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test Evohome's set_zone_override service (for a heating zone)."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        zone_id = evo.zone_id

        freezer.move_to("2024-07-10T12:00:00+00:00")

        # EvoZoneMode.PERMANENT_OVERRIDE
        with patch("evohomeasync2.zone.Zone.set_temperature") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_ZONE_OVERRIDE,
                {ATTR_SETPOINT: 19.5},
                target={ATTR_ENTITY_ID: zone_id},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(19.5, until=None)

        # EvoZoneMode.TEMPORARY_OVERRIDE
        with patch("evohomeasync2.zone.Zone.set_temperature") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_ZONE_OVERRIDE,
                {
                    ATTR_SETPOINT: 19.5,
                    ATTR_DURATION: {"minutes": 135},
                },
                target={ATTR_ENTITY_ID: zone_id},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(
                19.5, until=datetime(2024, 7, 10, 14, 15, tzinfo=UTC)
            )


@test
async def set_zone_override_advance(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test Evohome's set_zone_override service with duration=0.

    The override is temporary until the next schedule change.
    """
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        zone_id = evo.zone_id

        freezer.move_to("2024-05-10T12:15:00+00:00")
        expected_until = datetime(2024, 5, 10, 21, 10, tzinfo=UTC)

        # Simulate the schedule not yet having been fetched
        entities = hass.data[DATA_DOMAIN_PLATFORM_ENTITIES].get(
            (CLIMATE_DOMAIN, DOMAIN), {}
        )

        zone_entity: EvoZone = entities[zone_id]  # type: ignore[assignment]
        zone_entity._schedule = None
        zone_entity._setpoints = {}

        with patch("evohomeasync2.zone.Zone.set_temperature") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_ZONE_OVERRIDE,
                {ATTR_SETPOINT: 19.5, ATTR_DURATION: {"minutes": 0}},
                target={ATTR_ENTITY_ID: zone_id},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(19.5, until=expected_until)

        expect(zone_entity.setpoints["next_sp_from"]).to_equal(expected_until)


@test
async def set_zone_override_legacy(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test Evohome's set_zone_override service with the legacy entity_id."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        zone_id = evo.zone_id

        freezer.move_to("2024-07-10T12:00:00+00:00")

        # EvoZoneMode.PERMANENT_OVERRIDE
        with patch("evohomeasync2.zone.Zone.set_temperature") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_ZONE_OVERRIDE,
                {ATTR_ENTITY_ID: zone_id, ATTR_SETPOINT: 19.5},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(19.5, until=None)

        # EvoZoneMode.TEMPORARY_OVERRIDE
        with patch("evohomeasync2.zone.Zone.set_temperature") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_ZONE_OVERRIDE,
                {
                    ATTR_ENTITY_ID: zone_id,
                    ATTR_SETPOINT: 19.5,
                    ATTR_DURATION: {"minutes": 135},
                },
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(
                19.5, until=datetime(2024, 7, 10, 14, 15, tzinfo=UTC)
            )


@test.cases(
    test.case(
        "clear_zone_override",
        service=EvoService.CLEAR_ZONE_OVERRIDE,
        service_data={},
    ),
    test.case(
        "set_zone_override",
        service=EvoService.SET_ZONE_OVERRIDE,
        service_data={ATTR_SETPOINT: 19.5},
    ),
)
async def zone_services_with_ctl_id(
    service: EvoService,
    service_data: dict[str, Any],
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test calling zone-only service calls with a non-zone entity_id fails."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        ctl_id = evo.ctl_id

        raised: ServiceValidationError | None = None
        try:
            await hass.services.async_call(
                DOMAIN,
                service,
                service_data,
                target={ATTR_ENTITY_ID: ctl_id},
                blocking=True,
            )
        except ServiceValidationError as exc:
            raised = exc

        expect(raised).not_.to_be_none()
        expect(raised.translation_key).to_equal("zone_only_service")
        expect(raised.translation_placeholders).to_equal({"service": service})


@test
async def controller_services_with_zone_id(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test calling controller-only service calls with a zone entity_id fails."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        zone_id = evo.zone_id

        raised: ServiceValidationError | None = None
        try:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_SYSTEM_MODE,
                {ATTR_MODE: "Auto", ATTR_ENTITY_ID: zone_id},
                blocking=True,
            )
        except ServiceValidationError as exc:
            raised = exc

        expect(raised).not_.to_be_none()
        expect(raised.translation_key).to_equal("controller_only_service")
        expect(raised.translation_placeholders).to_equal(
            {"service": EvoService.SET_SYSTEM_MODE}
        )


@test
async def set_system_mode_entity_not_found(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test set_system_mode with non-existent entity_id raises entity_not_found."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry):
        non_existent_entity_id = "climate.non_existent_entity"

        raised: ServiceValidationError | None = None
        try:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_SYSTEM_MODE,
                {ATTR_MODE: "Auto", ATTR_ENTITY_ID: non_existent_entity_id},
                blocking=True,
            )
        except ServiceValidationError as exc:
            raised = exc

        expect(raised).not_.to_be_none()
        expect(raised.translation_key).to_equal("entity_not_found")
        expect(raised.translation_placeholders).to_equal(
            {ATTR_ENTITY_ID: non_existent_entity_id}
        )


@test.cases(
    test.case(
        "mode_not_supported",
        service_data={ATTR_MODE: "NotARealMode"},
        expected_translation_key="mode_not_supported",
    ),
    test.case(
        "mode_cant_be_temporary",
        service_data={ATTR_MODE: "Auto", ATTR_DURATION: {"hours": 1}},
        expected_translation_key="mode_cant_be_temporary",
    ),
    test.case(
        "mode_cant_have_period",
        service_data={ATTR_MODE: "AutoWithEco", ATTR_PERIOD: {"days": 1}},
        expected_translation_key="mode_cant_have_period",
    ),
    test.case(
        "mode_cant_have_duration",
        service_data={ATTR_MODE: "DayOff", ATTR_DURATION: {"hours": 1}},
        expected_translation_key="mode_cant_have_duration",
    ),
)
async def set_system_mode_validator(
    service_data: dict[str, Any],
    expected_translation_key: str,
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test ServiceValidationError for controller system mode validation cases."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry):
        raised: ServiceValidationError | None = None
        try:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_SYSTEM_MODE,
                service_data,
                blocking=True,
            )
        except ServiceValidationError as exc:
            raised = exc

        expect(raised).not_.to_be_none()
        expect(raised.translation_key).to_equal(expected_translation_key)
        expect(raised.translation_placeholders).to_equal(
            {ATTR_MODE: service_data[ATTR_MODE]}
        )


@test
async def set_dhw_override(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test Evohome's set_dhw_override service (for a DHW zone)."""
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        dhw_id = evo.dhw_id
        expect(dhw_id).not_.to_be_none()

        freezer.move_to("2024-07-10T12:00:00+00:00")

        # EvoZoneMode.PERMANENT_OVERRIDE (off)
        with patch("evohomeasync2.hotwater.HotWater.set_off") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_DHW_OVERRIDE,
                {ATTR_STATE: False},
                target={ATTR_ENTITY_ID: dhw_id},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(until=None)

        # EvoZoneMode.TEMPORARY_OVERRIDE (on)
        with patch("evohomeasync2.hotwater.HotWater.set_on") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_DHW_OVERRIDE,
                {ATTR_STATE: True, ATTR_DURATION: {"minutes": 135}},
                target={ATTR_ENTITY_ID: dhw_id},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(
                until=datetime(2024, 7, 10, 14, 15, tzinfo=UTC)
            )


@test
async def set_dhw_override_advance(
    hass: HomeAssistant = Depends(hass_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _network: None = Depends(mock_network_fx),
) -> None:
    """Test Evohome's set_dhw_override service with duration=0.

    The override is temporary until the next schedule change.
    """
    freezer.move_to("2024-07-10T12:00:00Z")
    async with setup_evo_for_test(hass, "default", entity_registry) as evo:
        dhw_id = evo.dhw_id
        expect(dhw_id).not_.to_be_none()

        freezer.move_to("2024-05-10T12:15:00+00:00")
        expected_until = datetime(2024, 5, 10, 15, 30, tzinfo=UTC)

        entities = hass.data[DATA_DOMAIN_PLATFORM_ENTITIES].get(
            (WATER_HEATER_DOMAIN, DOMAIN), {}
        )

        dhw_entity: EvoDHW = entities[dhw_id]  # type: ignore[assignment]
        dhw_entity._schedule = None
        dhw_entity._setpoints = {}

        with patch("evohomeasync2.hotwater.HotWater.set_on") as mock_fcn:
            await hass.services.async_call(
                DOMAIN,
                EvoService.SET_DHW_OVERRIDE,
                {ATTR_STATE: True, ATTR_DURATION: {"minutes": 0}},
                target={ATTR_ENTITY_ID: dhw_id},
                blocking=True,
            )

            mock_fcn.assert_awaited_once_with(until=expected_until)

        expect(dhw_entity.setpoints["next_sp_from"]).to_equal(expected_until)
