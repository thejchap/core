"""The tests for the Command line Binary sensor platform."""

import asyncio
from datetime import timedelta
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.command_line.binary_sensor import CommandBinarySensor
from homeassistant.components.command_line.const import DOMAIN
from homeassistant.components.homeassistant import (
    DOMAIN as HA_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.util import dt as dt_util

from . import mock_asyncio_subprocess_run
from ._fixtures import async_load_yaml_integration

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def setup_integration_yaml(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sensor setup."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "binary_sensor": {
                        "name": "Test",
                        "command": "echo 1",
                        "payload_on": "1",
                        "payload_off": "0",
                        "command_timeout": 15,
                    }
                }
            ]
        },
    )

    entity_state = hass.states.get("binary_sensor.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_ON)
    expect(entity_state.name).to_equal("Test")


@test
async def setup_platform_yaml(
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test setting up the platform with platform yaml."""
    await setup.async_setup_component(
        hass,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "command_line",
                "command": "echo 1",
                "payload_on": "1",
                "payload_off": "0",
            }
        },
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(0)

    issue = issue_registry.async_get_issue(
        DOMAIN, "binary_sensor_platform_yaml_not_supported"
    )
    expect(issue).not_.to_be_none()
    expect(issue.severity).to_equal(ir.IssueSeverity.ERROR)
    expect(issue.translation_placeholders).to_equal({"platform": BINARY_SENSOR_DOMAIN})


@test
async def template(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test setting the state with a template."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "binary_sensor": {
                        "name": "Test",
                        "command": "echo 10",
                        "payload_on": "1.0",
                        "payload_off": "0",
                        "value_template": "{{ value | multiply(0.1) }}",
                        "icon": (
                            '{% if this.attributes.icon=="mdi:icon2" %} mdi:icon1 {% else %} mdi:icon2 {% endif %}'
                        ),
                    }
                }
            ]
        },
    )

    entity_state = hass.states.get("binary_sensor.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_ON)
    expect(entity_state.attributes.get("icon")).to_equal("mdi:icon2")

    async_fire_time_changed(hass, dt_util.now() + timedelta(seconds=30))
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("binary_sensor.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_ON)
    expect(entity_state.attributes.get("icon")).to_equal("mdi:icon1")


@test
async def sensor_off(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test setting the state with a template."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "binary_sensor": {
                        "name": "Test",
                        "command": "echo 0",
                        "payload_on": "1",
                        "payload_off": "0",
                    }
                }
            ]
        },
    )

    entity_state = hass.states.get("binary_sensor.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_OFF)


@test
async def unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unique_id option and if it only creates one binary sensor per id."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "binary_sensor": {
                        "unique_id": "unique",
                        "command": "echo 0",
                    }
                },
                {
                    "binary_sensor": {
                        "unique_id": "not-so-unique-anymore",
                        "command": "echo 1",
                    }
                },
                {
                    "binary_sensor": {
                        "unique_id": "not-so-unique-anymore",
                        "command": "echo 2",
                    }
                },
            ]
        },
    )

    expect(len(hass.states.async_all())).to_equal(2)

    expect(len(entity_registry.entities)).to_equal(2)
    expect(
        entity_registry.async_get_entity_id("binary_sensor", "command_line", "unique")
    ).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(
            "binary_sensor", "command_line", "not-so-unique-anymore"
        )
    ).not_.to_be_none()


@test
async def return_code(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test setting the state with a template."""
    await setup.async_setup_component(
        hass,
        DOMAIN,
        {
            "command_line": [
                {
                    "binary_sensor": {
                        "command": "exit 33",
                    }
                }
            ]
        },
    )
    await hass.async_block_till_done()
    expect("return code 33" in caplog.text).to_be_truthy()


@test
async def updating_to_often(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling updating when command already running."""

    wait_till_event = asyncio.Event()
    wait_till_event.set()
    called = []

    class MockCommandBinarySensor(CommandBinarySensor):
        """Mock entity that updates."""

        async def _async_update(self) -> None:
            """Update the entity."""
            called.append(1)
            # Wait till event is set
            await wait_till_event.wait()

    with patch(
        "homeassistant.components.command_line.binary_sensor.CommandBinarySensor",
        side_effect=MockCommandBinarySensor,
    ):
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                "command_line": [
                    {
                        "binary_sensor": {
                            "name": "Test",
                            "command": "echo 1",
                            "payload_on": "1",
                            "payload_off": "0",
                            "scan_interval": 10,
                        }
                    }
                ]
            },
        )
        await hass.async_block_till_done()

    expect(called).to_be_truthy()
    async_fire_time_changed(hass, dt_util.now() + timedelta(seconds=15))
    wait_till_event.set()
    await asyncio.sleep(0)
    expect(
        "Updating Command Line Binary Sensor Test took longer than the scheduled update interval"
        not in caplog.text
    ).to_be_truthy()

    # Simulate update takes too long
    wait_till_event.clear()
    async_fire_time_changed(hass, dt_util.now() + timedelta(seconds=10))
    await asyncio.sleep(0)
    async_fire_time_changed(hass, dt_util.now() + timedelta(seconds=10))
    wait_till_event.set()
    await asyncio.sleep(0)

    expect(
        "Updating Command Line Binary Sensor Test took longer than the scheduled update interval"
        in caplog.text
    ).to_be_truthy()


@test
async def updating_manually(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling manual updating using homeassistant udate_entity service."""
    await setup.async_setup_component(hass, HA_DOMAIN, {})
    called = []

    class MockCommandBinarySensor(CommandBinarySensor):
        """Mock entity that updates."""

        async def _async_update(self) -> None:
            """Update."""
            called.append(1)

    with patch(
        "homeassistant.components.command_line.binary_sensor.CommandBinarySensor",
        side_effect=MockCommandBinarySensor,
    ):
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                "command_line": [
                    {
                        "binary_sensor": {
                            "name": "Test",
                            "command": "echo 1",
                            "payload_on": "1",
                            "payload_off": "0",
                            "scan_interval": 10,
                        }
                    }
                ]
            },
        )
        await hass.async_block_till_done()

    expect(called).to_be_truthy()
    called.clear()

    await hass.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: ["binary_sensor.test"]},
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(called).to_be_truthy()


@test
async def availability(
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test availability."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "binary_sensor": {
                        "name": "Test",
                        "command": "echo 10",
                        "payload_on": "1.0",
                        "payload_off": "0.0",
                        "value_template": "{{ value | multiply(0.1) }}",
                        "availability": '{{ "sensor.input1" | has_value }}',
                        "icon": 'mdi:{{ states("sensor.input1") }}',
                    }
                }
            ]
        },
    )

    hass.states.async_set("sensor.input1", STATE_ON)
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("binary_sensor.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_ON)
    expect(entity_state.attributes["icon"]).to_equal("mdi:on")

    hass.states.async_set("sensor.input1", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"0"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("binary_sensor.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_UNAVAILABLE)
    expect("icon" not in entity_state.attributes).to_be_truthy()

    hass.states.async_set("sensor.input1", STATE_OFF)
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"0"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("binary_sensor.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_OFF)
    expect(entity_state.attributes["icon"]).to_equal("mdi:off")


@test
async def availability_blocks_value_template(
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test availability blocks value_template from rendering."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "binary_sensor": {
                        "name": "Test",
                        "command": "echo 10",
                        "payload_on": "1.0",
                        "payload_off": "0.0",
                        "value_template": "{{ x - 1 }}",
                        "availability": "{{ value == '50' }}",
                    }
                }
            ]
        },
    )

    error = "Error parsing value for binary_sensor.test: 'x' is undefined"
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"51\n"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(error not in caplog.text).to_be_truthy()

    entity_state = hass.states.get("binary_sensor.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_UNAVAILABLE)

    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"50\n"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(error in caplog.text).to_be_truthy()
