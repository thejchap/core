"""The tests for Core components."""

from unittest.mock import Mock, patch

import voluptuous as vol
import yaml

from tryke import Depends, expect, fixture, test

from homeassistant import config, core as ha
from homeassistant.components.homeassistant import (
    ATTR_ENTRY_ID,
    ATTR_SAFE_MODE,
    DOMAIN,
    SERVICE_CHECK_CONFIG,
    SERVICE_HOMEASSISTANT_RESTART,
    SERVICE_HOMEASSISTANT_STOP,
    SERVICE_RELOAD_ALL,
    SERVICE_RELOAD_CORE_CONFIG,
    SERVICE_RELOAD_CUSTOM_TEMPLATES,
    SERVICE_SET_LOCATION,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    ENTITY_MATCH_NONE,
    EVENT_CORE_CONFIG_UPDATE,
    EVENT_HOMEASSISTANT_STARTED,
    SERVICE_SAVE_PERSISTENT_STATES,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.helpers import entity, entity_registry as er, issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    MockEntityPlatform,
    MockUser,
    async_capture_events,
    async_mock_service,
    patch_yaml_files,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    hass_read_only_user as hass_read_only_user_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    return 0


@test
async def turn_on_without_entities(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test turn_on method without entities."""
    await async_setup_component(hass, ha.DOMAIN, {})
    calls = async_mock_service(hass, "light", SERVICE_TURN_ON)
    await hass.services.async_call(ha.DOMAIN, SERVICE_TURN_ON, blocking=True)
    expect(len(calls)).to_be(0)


@test
async def turn_on(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test turn_on method."""
    await async_setup_component(hass, ha.DOMAIN, {})
    calls = async_mock_service(hass, "light", SERVICE_TURN_ON)
    await hass.services.async_call(
        ha.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: "light.Ceiling"}, blocking=True
    )
    expect(len(calls)).to_be(1)


@test
async def turn_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test turn_off method."""
    await async_setup_component(hass, ha.DOMAIN, {})
    calls = async_mock_service(hass, "light", SERVICE_TURN_OFF)
    await hass.services.async_call(
        ha.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "light.Bowl"}, blocking=True
    )
    expect(len(calls)).to_be(1)


@test
async def toggle(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test toggle method."""
    await async_setup_component(hass, ha.DOMAIN, {})
    calls = async_mock_service(hass, "light", SERVICE_TOGGLE)
    await hass.services.async_call(
        ha.DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: "light.Bowl"}, blocking=True
    )
    expect(len(calls)).to_be(1)


@test
async def reload_core_conf(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reload core conf service."""
    with patch("homeassistant.config.os.path.isfile", Mock(return_value=True)):
        await async_setup_component(hass, ha.DOMAIN, {})
        ent = entity.Entity()
        ent.entity_id = "test.entity"
        ent.hass = hass
        platform = MockEntityPlatform(hass, domain="test", platform_name="test")
        await platform.async_add_entities([ent])
        ent.async_write_ha_state()

        state = hass.states.get("test.entity")
        expect(state).not_.to_be(None)
        expect(state.state).to_equal("unknown")
        expect(state.attributes).to_equal({})

        files = {
            config.YAML_CONFIG_FILE: yaml.dump(
                {
                    ha.DOMAIN: {
                        "country": "SE",
                        "latitude": 10,
                        "longitude": 20,
                        "customize": {"test.Entity": {"hello": "world"}},
                    }
                }
            )
        }
        with patch_yaml_files(files, True):
            await hass.services.async_call(
                ha.DOMAIN, SERVICE_RELOAD_CORE_CONFIG, blocking=True
            )

        expect(hass.config.latitude).to_equal(10)
        expect(hass.config.longitude).to_equal(20)

        ent.async_write_ha_state()

        state = hass.states.get("test.entity")
        expect(state).not_.to_be(None)
        expect(state.state).to_equal("unknown")
        expect(state.attributes.get("hello")).to_equal("world")


@test
async def reload_core_with_wrong_conf(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reload core conf service."""
    with (
        patch("homeassistant.config.os.path.isfile", Mock(return_value=True)),
        patch("homeassistant.components.homeassistant._LOGGER.error") as mock_error,
        patch(
            "homeassistant.core_config.async_process_ha_core_config"
        ) as mock_process,
    ):
        files = {config.YAML_CONFIG_FILE: yaml.dump(["invalid", "config"])}
        await async_setup_component(hass, ha.DOMAIN, {})
        with patch_yaml_files(files, True):
            await hass.services.async_call(
                ha.DOMAIN, SERVICE_RELOAD_CORE_CONFIG, blocking=True
            )

        expect(mock_error.called).to_be(True)
        expect(mock_process.called).to_be(False)


@test
async def restart_homeassistant_wrong_conf(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test restart service with error."""
    with (
        patch(
            "homeassistant.core.HomeAssistant.async_stop", return_value=None
        ) as mock_restart,
        patch(
            "homeassistant.config.async_check_ha_config_file",
            side_effect=HomeAssistantError("Test error"),
        ) as mock_check,
    ):
        await async_setup_component(hass, ha.DOMAIN, {})
        async with expect_raises_async(HomeAssistantError, match="Test error"):
            await hass.services.async_call(
                ha.DOMAIN, SERVICE_HOMEASSISTANT_RESTART, blocking=True
            )
        expect(mock_check.called).to_be(True)
        expect(mock_restart.called).to_be(False)


@test
async def check_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test stop service."""
    with (
        patch(
            "homeassistant.core.HomeAssistant.async_stop", return_value=None
        ) as mock_stop,
        patch(
            "homeassistant.config.async_check_ha_config_file", return_value=None
        ) as mock_check,
    ):
        await async_setup_component(hass, ha.DOMAIN, {})
        await hass.services.async_call(ha.DOMAIN, SERVICE_CHECK_CONFIG, blocking=True)
        expect(mock_check.called).to_be(True)
        expect(mock_stop.called).to_be(False)


@test
async def turn_on_skips_domains_without_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test if turn_on is blocking domain with no service."""
    await async_setup_component(hass, "homeassistant", {})
    async_mock_service(hass, "light", SERVICE_TURN_ON)
    hass.states.async_set("light.Bowl", STATE_ON)
    hass.states.async_set("light.Ceiling", STATE_OFF)

    service_call = ha.ServiceCall(
        hass,
        "homeassistant",
        "turn_on",
        {"entity_id": ["light.test", "sensor.bla", "binary_sensor.blub", "light.bla"]},
    )
    service = hass.services.async_services_for_domain("homeassistant")["turn_on"]

    with patch(
        "homeassistant.core.ServiceRegistry.async_call",
        return_value=None,
    ) as mock_call:
        await service.job.target(service_call)

    expect(mock_call.call_count).to_be(1)
    expect(mock_call.call_args_list[0][0]).to_equal(
        (
            "light",
            "turn_on",
            {"entity_id": ["light.bla", "light.test"]},
        )
    )
    expect(mock_call.call_args_list[0][1]).to_equal(
        {
            "blocking": True,
            "context": service_call.context,
        }
    )
    expect(
        "The service homeassistant.turn_on does not support entities binary_sensor.blub, sensor.bla"
        in caplog.text
    ).to_be(True)


@test
async def entity_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test being able to call entity update."""
    await async_setup_component(hass, "homeassistant", {})

    with patch(
        "homeassistant.components.homeassistant.async_update_entity",
        return_value=None,
    ) as mock_update:
        await hass.services.async_call(
            "homeassistant",
            "update_entity",
            {"entity_id": ["light.kitchen"]},
            blocking=True,
        )

    expect(len(mock_update.mock_calls)).to_be(1)
    expect(mock_update.mock_calls[0][1][1]).to_equal("light.kitchen")


@test
async def setting_location(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting the location."""
    await async_setup_component(hass, "homeassistant", {})
    events = async_capture_events(hass, EVENT_CORE_CONFIG_UPDATE)
    expect(hass.config.latitude != 30).to_be(True)
    expect(hass.config.longitude != 40).to_be(True)
    elevation = hass.config.elevation
    expect(elevation != 50).to_be(True)
    await hass.services.async_call(
        "homeassistant",
        SERVICE_SET_LOCATION,
        {"latitude": 30, "longitude": 40},
        blocking=True,
    )
    expect(len(events)).to_be(1)
    expect(hass.config.latitude).to_equal(30)
    expect(hass.config.longitude).to_equal(40)
    expect(hass.config.elevation).to_equal(elevation)

    await hass.services.async_call(
        "homeassistant",
        SERVICE_SET_LOCATION,
        {"latitude": 30, "longitude": 40, "elevation": 50},
        blocking=True,
    )
    expect(hass.config.latitude).to_equal(30)
    expect(hass.config.longitude).to_equal(40)
    expect(hass.config.elevation).to_equal(50)

    await hass.services.async_call(
        "homeassistant",
        SERVICE_SET_LOCATION,
        {"latitude": 30, "longitude": 40, "elevation": 0},
        blocking=True,
    )
    expect(hass.config.latitude).to_equal(30)
    expect(hass.config.longitude).to_equal(40)
    expect(hass.config.elevation).to_equal(0)


@test
async def require_admin(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fixture),
) -> None:
    """Test services requiring admin."""
    await async_setup_component(hass, "homeassistant", {})

    for service in (
        SERVICE_HOMEASSISTANT_RESTART,
        SERVICE_HOMEASSISTANT_STOP,
        SERVICE_CHECK_CONFIG,
        SERVICE_RELOAD_CORE_CONFIG,
    ):
        async with expect_raises_async(Unauthorized):
            await hass.services.async_call(
                ha.DOMAIN,
                service,
                {},
                context=ha.Context(user_id=hass_read_only_user.id),
                blocking=True,
            )

    async with expect_raises_async(Unauthorized):
        await hass.services.async_call(
            ha.DOMAIN,
            SERVICE_SET_LOCATION,
            {"latitude": 0, "longitude": 0},
            context=ha.Context(user_id=hass_read_only_user.id),
            blocking=True,
        )


@test
async def turn_on_off_toggle_schema(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fixture),
) -> None:
    """Test the schemas for the turn on/off/toggle services."""
    await async_setup_component(hass, "homeassistant", {})

    for service in SERVICE_TURN_ON, SERVICE_TURN_OFF, SERVICE_TOGGLE:
        for invalid in None, "nothing", ENTITY_MATCH_ALL, ENTITY_MATCH_NONE:
            async with expect_raises_async(vol.Invalid):
                await hass.services.async_call(
                    ha.DOMAIN,
                    service,
                    {"entity_id": invalid},
                    context=ha.Context(user_id=hass_read_only_user.id),
                    blocking=True,
                )


@test
async def not_allowing_recursion(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we do not allow recursion."""
    await async_setup_component(hass, "homeassistant", {})

    for service in SERVICE_TURN_ON, SERVICE_TURN_OFF, SERVICE_TOGGLE:
        await hass.services.async_call(
            ha.DOMAIN,
            service,
            {"entity_id": "homeassistant.light"},
            blocking=True,
        )
        expect(
            f"Called service homeassistant.{service} with invalid entities homeassistant.light"
            in caplog.text
        ).to_be(True)


@test
async def reload_config_entry_by_entity_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test being able to reload a config entry by entity_id."""
    await async_setup_component(hass, "homeassistant", {})
    entry1 = MockConfigEntry(domain="mockdomain")
    entry1.add_to_hass(hass)
    entry2 = MockConfigEntry(domain="mockdomain")
    entry2.add_to_hass(hass)
    reg_entity1 = entity_registry.async_get_or_create(
        "binary_sensor", "powerwall", "battery_charging", config_entry=entry1
    )
    reg_entity2 = entity_registry.async_get_or_create(
        "binary_sensor", "powerwall", "battery_status", config_entry=entry2
    )
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload",
        return_value=None,
    ) as mock_reload:
        await hass.services.async_call(
            "homeassistant",
            "reload_config_entry",
            {"entity_id": f"{reg_entity1.entity_id},{reg_entity2.entity_id}"},
            blocking=True,
        )

    expect(len(mock_reload.mock_calls)).to_be(2)
    expect(
        {mock_reload.mock_calls[0][1][0], mock_reload.mock_calls[1][1][0]}
    ).to_equal({entry1.entry_id, entry2.entry_id})

    async with expect_raises_async(ValueError):
        await hass.services.async_call(
            "homeassistant",
            "reload_config_entry",
            {"entity_id": "unknown.entity_id"},
            blocking=True,
        )


@test
async def reload_config_entry_by_entry_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test being able to reload a config entry by config entry id."""
    await async_setup_component(hass, "homeassistant", {})

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload",
        return_value=None,
    ) as mock_reload:
        await hass.services.async_call(
            "homeassistant",
            "reload_config_entry",
            {ATTR_ENTRY_ID: "8955375327824e14ba89e4b29cc3ec9a"},
            blocking=True,
        )

    expect(len(mock_reload.mock_calls)).to_be(1)
    expect(mock_reload.mock_calls[0][1][0]).to_equal(
        "8955375327824e14ba89e4b29cc3ec9a"
    )


@test.cases(
    test.case("restart", service=SERVICE_HOMEASSISTANT_RESTART),
    test.case("stop", service=SERVICE_HOMEASSISTANT_STOP),
)
async def raises_when_db_upgrade_in_progress(
    service: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test an exception is raised when the database migration is in progress."""
    await async_setup_component(hass, "homeassistant", {})

    with patch(
        "homeassistant.helpers.recorder.async_migration_in_progress",
        return_value=True,
    ) as mock_async_migration_in_progress:
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                "homeassistant",
                service,
                blocking=True,
            )
    expect("The system cannot" in caplog.text).to_be(True)
    expect("while a database upgrade is in progress" in caplog.text).to_be(True)

    expect(mock_async_migration_in_progress.called).to_be(True)
    caplog.clear()

    with (
        patch(
            "homeassistant.helpers.recorder.async_migration_in_progress",
            return_value=False,
        ) as mock_async_migration_in_progress,
        patch("homeassistant.config.async_check_ha_config_file", return_value=None),
    ):
        await hass.services.async_call(
            "homeassistant",
            service,
            blocking=True,
        )
        expect("The system cannot" not in caplog.text).to_be(True)
        expect("while a database upgrade in progress" not in caplog.text).to_be(True)

    expect(mock_async_migration_in_progress.called).to_be(True)


@test
async def raises_when_config_is_invalid(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test an exception is raised when the configuration is invalid."""
    await async_setup_component(hass, "homeassistant", {})

    with (
        patch(
            "homeassistant.helpers.recorder.async_migration_in_progress",
            return_value=False,
        ),
        patch(
            "homeassistant.config.async_check_ha_config_file", return_value=["Error 1"]
        ) as mock_async_check_ha_config_file,
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                "homeassistant",
                SERVICE_HOMEASSISTANT_RESTART,
                blocking=True,
            )
    expect("The system cannot" in caplog.text).to_be(True)
    expect("because the configuration is not valid" in caplog.text).to_be(True)
    expect("Error 1" in caplog.text).to_be(True)

    expect(mock_async_check_ha_config_file.called).to_be(True)
    caplog.clear()

    with (
        patch(
            "homeassistant.helpers.recorder.async_migration_in_progress",
            return_value=False,
        ),
        patch(
            "homeassistant.config.async_check_ha_config_file", return_value=None
        ) as mock_async_check_ha_config_file,
    ):
        await hass.services.async_call(
            "homeassistant",
            SERVICE_HOMEASSISTANT_RESTART,
            blocking=True,
        )

    expect(mock_async_check_ha_config_file.called).to_be(True)


@test.cases(
    test.case("default", service_data={}, safe_mode_enabled=False),
    test.case(
        "safe_mode_false", service_data={ATTR_SAFE_MODE: False}, safe_mode_enabled=False
    ),
    test.case(
        "safe_mode_true", service_data={ATTR_SAFE_MODE: True}, safe_mode_enabled=True
    ),
)
async def restart_homeassistant(
    service_data: dict,
    safe_mode_enabled: bool,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can restart when there is no configuration error."""
    await async_setup_component(hass, "homeassistant", {})
    with (
        patch(
            "homeassistant.config.async_check_ha_config_file", return_value=None
        ) as mock_check,
        patch("homeassistant.config.async_enable_safe_mode") as mock_safe_mode,
        patch(
            "homeassistant.core.HomeAssistant.async_stop", return_value=None
        ) as mock_restart,
    ):
        await hass.services.async_call(
            "homeassistant",
            SERVICE_HOMEASSISTANT_RESTART,
            service_data,
            blocking=True,
        )
        expect(mock_check.called).to_be(True)
        await hass.async_block_till_done()
        expect(mock_restart.called).to_be(True)
        expect(mock_safe_mode.called).to_be(safe_mode_enabled)


@test
async def stop_homeassistant(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can stop when there is a configuration error."""
    await async_setup_component(hass, "homeassistant", {})
    with (
        patch(
            "homeassistant.config.async_check_ha_config_file", return_value=None
        ) as mock_check,
        patch(
            "homeassistant.core.HomeAssistant.async_stop", return_value=None
        ) as mock_restart,
    ):
        await hass.services.async_call(
            "homeassistant",
            SERVICE_HOMEASSISTANT_STOP,
            blocking=True,
        )
        expect(mock_check.called).to_be(False)
        await hass.async_block_till_done()
        expect(mock_restart.called).to_be(True)


@test
async def save_persistent_states(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can call save_persistent_states."""
    await async_setup_component(hass, "homeassistant", {})
    with patch(
        "homeassistant.helpers.restore_state.RestoreStateData.async_save_persistent_states",
        return_value=None,
    ) as mock_save:
        await hass.services.async_call(
            "homeassistant",
            SERVICE_SAVE_PERSISTENT_STATES,
            blocking=True,
        )
        expect(mock_save.called).to_be(True)


@test
async def reload_custom_templates(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can call reload_custom_templates."""
    await async_setup_component(hass, "homeassistant", {})
    with patch(
        "homeassistant.components.homeassistant.async_load_custom_templates",
        return_value=None,
    ) as mock_load_custom_templates:
        await hass.services.async_call(
            "homeassistant",
            SERVICE_RELOAD_CUSTOM_TEMPLATES,
            blocking=True,
        )
        expect(mock_load_custom_templates.called).to_be(True)


@test
async def reload_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test reload_all service."""
    await async_setup_component(hass, "homeassistant", {})
    test1 = async_mock_service(hass, "test1", "reload")
    test2 = async_mock_service(hass, "test2", "reload")
    no_reload = async_mock_service(hass, "test3", "not_reload")
    notify = async_mock_service(hass, "notify", "reload")
    core_config = async_mock_service(hass, "homeassistant", "reload_core_config")
    themes = async_mock_service(hass, "frontend", "reload_themes")
    jinja = async_mock_service(hass, "homeassistant", "reload_custom_templates")

    with patch(
        "homeassistant.config.async_check_ha_config_file",
        return_value=None,
    ) as mock_async_check_ha_config_file:
        await hass.services.async_call(
            "homeassistant",
            SERVICE_RELOAD_ALL,
            blocking=True,
        )

    expect(mock_async_check_ha_config_file.called).to_be(True)
    expect(len(test1)).to_be(1)
    expect(len(test2)).to_be(1)
    expect(len(no_reload)).to_be(0)
    expect(len(notify)).to_be(0)
    expect(len(core_config)).to_be(1)
    expect(len(themes)).to_be(1)

    with patch(
        "homeassistant.config.async_check_ha_config_file",
        return_value="Oh no, drama!",
    ) as mock_async_check_ha_config_file:
        async with expect_raises_async(
            HomeAssistantError,
            match=(
                "Cannot quick reload all YAML configurations because the configuration is "
                "not valid: Oh no, drama!"
            ),
        ):
            await hass.services.async_call(
                "homeassistant",
                SERVICE_RELOAD_ALL,
                blocking=True,
            )

    expect(mock_async_check_ha_config_file.called).to_be(True)
    expect(
        "The system cannot reload because the configuration is not valid: Oh no, drama!"
        in caplog.text
    ).to_be(True)

    expect(len(test1)).to_be(1)
    expect(len(test2)).to_be(1)
    expect(len(core_config)).to_be(1)
    expect(len(themes)).to_be(1)
    expect(len(jinja)).to_be(1)


@test.cases(
    test.case(
        "i386_unknown",
        arch="i386",
        bit_32=True,
        installation_type="Unknown",
        venv=False,
        expected_issues=[("unsupported_local_deps", None)],
    ),
    test.case(
        "armhf_unknown",
        arch="armhf",
        bit_32=True,
        installation_type="Unknown",
        venv=False,
        expected_issues=[("unsupported_local_deps", None)],
    ),
    test.case(
        "armv7_unknown",
        arch="armv7",
        bit_32=True,
        installation_type="Unknown",
        venv=False,
        expected_issues=[("unsupported_local_deps", None)],
    ),
    test.case(
        "aarch64_unknown",
        arch="aarch64",
        bit_32=False,
        installation_type="Unknown",
        venv=False,
        expected_issues=[("unsupported_local_deps", None)],
    ),
    test.case(
        "generic_x86_64_unknown",
        arch="generic-x86-64",
        bit_32=False,
        installation_type="Unknown",
        venv=False,
        expected_issues=[("unsupported_local_deps", None)],
    ),
    test.case(
        "i386_core",
        arch="i386",
        bit_32=True,
        installation_type="Home Assistant Core",
        venv=True,
        expected_issues=[
            (
                "deprecated_method_architecture",
                {"installation_type": "Core", "arch": "i386"},
            )
        ],
    ),
    test.case(
        "armhf_core",
        arch="armhf",
        bit_32=True,
        installation_type="Home Assistant Core",
        venv=True,
        expected_issues=[
            (
                "deprecated_method_architecture",
                {"installation_type": "Core", "arch": "armhf"},
            )
        ],
    ),
    test.case(
        "armv7_core",
        arch="armv7",
        bit_32=True,
        installation_type="Home Assistant Core",
        venv=True,
        expected_issues=[
            (
                "deprecated_method_architecture",
                {"installation_type": "Core", "arch": "armv7"},
            )
        ],
    ),
    test.case(
        "aarch64_core",
        arch="aarch64",
        bit_32=False,
        installation_type="Home Assistant Core",
        venv=True,
        expected_issues=[
            ("deprecated_method", {"installation_type": "Core", "arch": "aarch64"})
        ],
    ),
    test.case(
        "generic_x86_64_core",
        arch="generic-x86-64",
        bit_32=False,
        installation_type="Home Assistant Core",
        venv=True,
        expected_issues=[
            (
                "deprecated_method",
                {"installation_type": "Core", "arch": "generic-x86-64"},
            )
        ],
    ),
)
async def deprecated_installation_issue_core(
    arch: str,
    bit_32: bool,
    installation_type: str,
    venv: bool,
    expected_issues: list[tuple[str, dict[str, str | None]]],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test deprecated installation issue."""
    with (
        patch(
            "homeassistant.components.homeassistant.async_get_system_info",
            return_value={
                "installation_type": installation_type,
                "arch": arch,
                "docker": False,
                "virtualenv": venv,
            },
        ),
        patch(
            "homeassistant.components.homeassistant._is_32_bit",
            return_value=bit_32,
        ),
    ):
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    expect(len(issue_registry.issues)).to_be(len(expected_issues))
    for expected_issue, expected_placeholders in expected_issues:
        issue = issue_registry.async_get_issue(DOMAIN, expected_issue)
        expect(issue.domain).to_be(DOMAIN)
        expect(issue.severity).to_be(ir.IssueSeverity.WARNING)
        expect(issue.translation_placeholders).to_equal(expected_placeholders)


@test.cases(
    test.case("i386", arch="i386"),
    test.case("armv7", arch="armv7"),
    test.case("armhf", arch="armhf"),
)
async def deprecated_installation_issue_container_32bit(
    arch: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test deprecated installation issue."""
    with (
        patch(
            "homeassistant.components.homeassistant.async_get_system_info",
            return_value={
                "installation_type": "Home Assistant Container",
                "container_arch": arch,
                "arch": arch,
                "docker": True,
                "virtualenv": False,
            },
        ),
        patch(
            "homeassistant.components.homeassistant._is_32_bit",
            return_value=True,
        ),
    ):
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    expect(len(issue_registry.issues)).to_be(1)
    issue = issue_registry.async_get_issue(DOMAIN, "deprecated_container")
    expect(issue.domain).to_be(DOMAIN)
    expect(issue.severity).to_be(ir.IssueSeverity.WARNING)
    expect(issue.translation_placeholders).to_equal({"arch": arch})
