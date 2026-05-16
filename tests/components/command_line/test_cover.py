"""The tests the cover command line platform."""

import asyncio
from datetime import timedelta
import os
import tempfile
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.components.command_line import DOMAIN
from homeassistant.components.command_line.cover import CommandCover
from homeassistant.components.cover import (
    DOMAIN as COVER_DOMAIN,
    SCAN_INTERVAL,
    CoverState,
)
from homeassistant.components.homeassistant import (
    DOMAIN as HA_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_STOP_COVER,
    STATE_UNAVAILABLE,
)
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
async def setup_platform_yaml(
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test setting up the platform with platform yaml."""
    await setup.async_setup_component(
        hass,
        "cover",
        {
            "cover": {
                "platform": "command_line",
                "command": "echo 1",
                "payload_on": "1",
                "payload_off": "0",
            }
        },
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(0)
    issue = issue_registry.async_get_issue(DOMAIN, "cover_platform_yaml_not_supported")
    expect(issue).not_.to_be_none()
    expect(issue.severity).to_equal(ir.IssueSeverity.ERROR)
    expect(issue.translation_placeholders).to_equal({"platform": COVER_DOMAIN})


@test
async def no_poll_when_cover_has_no_command_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the cover does not polls when there's no state command."""

    with mock_asyncio_subprocess_run(b"50\n") as mock_subprocess_run:
        expect(
            await setup.async_setup_component(
                hass,
                COVER_DOMAIN,
                {
                    COVER_DOMAIN: [
                        {"platform": "command_line", "covers": {"test": {}}},
                    ]
                },
            )
        ).to_be_truthy()
        async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
        await hass.async_block_till_done()
        expect(mock_subprocess_run.called).to_be_falsy()


@test
async def poll_when_cover_has_command_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the cover polls when there's a state command."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "cover": {
                        "command_state": "echo state",
                        "name": "Test",
                    },
                }
            ]
        },
    )

    with mock_asyncio_subprocess_run(b"50\n") as mock_subprocess_run:
        async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
        await hass.async_block_till_done()
        mock_subprocess_run.assert_called_once_with(
            "echo state",
            close_fds=False,
            stdout=-1,
        )


@test
async def state_value(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test with state value."""
    with tempfile.TemporaryDirectory() as tempdirname:
        path = os.path.join(tempdirname, "cover_status")
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                "command_line": [
                    {
                        "cover": {
                            "command_state": f"cat {path}",
                            "command_open": f"echo 1 > {path}",
                            "command_close": f"echo 1 > {path}",
                            "command_stop": f"echo 0 > {path}",
                            "value_template": "{{ value }}",
                            "name": "Test",
                        }
                    }
                ]
            },
        )
        await hass.async_block_till_done()

        entity_state = hass.states.get("cover.test")
        expect(entity_state).not_.to_be_none()
        expect(entity_state.state).to_equal("unknown")

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: "cover.test"},
            blocking=True,
        )
        entity_state = hass.states.get("cover.test")
        expect(entity_state).not_.to_be_none()
        expect(entity_state.state).to_equal("open")

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: "cover.test"},
            blocking=True,
        )
        entity_state = hass.states.get("cover.test")
        expect(entity_state).not_.to_be_none()
        expect(entity_state.state).to_equal("open")

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_STOP_COVER,
            {ATTR_ENTITY_ID: "cover.test"},
            blocking=True,
        )
        entity_state = hass.states.get("cover.test")
        expect(entity_state).not_.to_be_none()
        expect(entity_state.state).to_equal("closed")


@test
async def move_cover_failure(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test command failure."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "cover": {
                        "command_open": "exit 1",
                        "name": "Test",
                    }
                }
            ]
        },
    )

    await hass.services.async_call(
        COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: "cover.test"}, blocking=True
    )
    expect("Command failed" in caplog.text).to_be_truthy()
    expect("return code 1" in caplog.text).to_be_truthy()


@test
async def unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unique_id option and if it only creates one cover per id."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "cover": {
                        "command_open": "echo open",
                        "command_close": "echo close",
                        "command_stop": "echo stop",
                        "unique_id": "unique",
                        "name": "Test",
                    }
                },
                {
                    "cover": {
                        "command_open": "echo open",
                        "command_close": "echo close",
                        "command_stop": "echo stop",
                        "unique_id": "not-so-unique-anymore",
                        "name": "Test2",
                    }
                },
                {
                    "cover": {
                        "command_open": "echo open",
                        "command_close": "echo close",
                        "command_stop": "echo stop",
                        "unique_id": "not-so-unique-anymore",
                        "name": "Test3",
                    }
                },
            ]
        },
    )

    expect(len(hass.states.async_all())).to_equal(2)
    expect(len(entity_registry.entities)).to_equal(2)
    expect(
        entity_registry.async_get_entity_id("cover", "command_line", "unique")
    ).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(
            "cover", "command_line", "not-so-unique-anymore"
        )
    ).not_.to_be_none()


@test
async def updating_to_often(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling updating when command already running."""

    called = []
    wait_till_event = asyncio.Event()
    wait_till_event.set()

    class MockCommandCover(CommandCover):
        """Mock entity that updates."""

        async def _async_update(self) -> None:
            """Update the entity."""
            called.append(1)
            await wait_till_event.wait()

    with patch(
        "homeassistant.components.command_line.cover.CommandCover",
        side_effect=MockCommandCover,
    ):
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                "command_line": [
                    {
                        "cover": {
                            "command_state": "echo 1",
                            "value_template": "{{ value }}",
                            "name": "Test",
                            "scan_interval": 10,
                        }
                    }
                ]
            },
        )
        await hass.async_block_till_done()

    expect(called).to_be_falsy()
    expect(
        "Updating Command Line Cover Test took longer than the scheduled update interval"
        not in caplog.text
    ).to_be_truthy()
    async_fire_time_changed(hass, dt_util.now() + timedelta(seconds=11))
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(called).to_be_truthy()
    called.clear()

    expect(
        "Updating Command Line Cover Test took longer than the scheduled update interval"
        not in caplog.text
    ).to_be_truthy()

    # Simulate update takes too long
    wait_till_event.clear()
    async_fire_time_changed(hass, dt_util.now() + timedelta(seconds=10))
    await asyncio.sleep(0)
    async_fire_time_changed(hass, dt_util.now() + timedelta(seconds=10))
    wait_till_event.set()

    # Finish processing update
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(called).to_be_truthy()
    expect(
        "Updating Command Line Cover Test took longer than the scheduled update interval"
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

    class MockCommandCover(CommandCover):
        """Mock entity that updates."""

        async def _async_update(self) -> None:
            """Update."""
            called.append(1)

    with patch(
        "homeassistant.components.command_line.cover.CommandCover",
        side_effect=MockCommandCover,
    ):
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                "command_line": [
                    {
                        "cover": {
                            "command_state": "echo 1",
                            "value_template": "{{ value }}",
                            "name": "Test",
                            "scan_interval": 10,
                        }
                    }
                ]
            },
        )
        await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.now() + timedelta(seconds=10))
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(called).to_be_truthy()
    called.clear()

    await hass.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: ["cover.test"]},
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
                    "cover": {
                        "command_state": "echo 10",
                        "name": "Test",
                        "value_template": "{{ value }}",
                        "availability": '{{ "sensor.input1" | has_value }}',
                        "icon": 'mdi:{{ states("sensor.input1") }}',
                    },
                }
            ]
        },
    )

    hass.states.async_set("sensor.input1", "on")
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("cover.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(CoverState.OPEN)
    expect(entity_state.attributes["icon"]).to_equal("mdi:on")

    hass.states.async_set("sensor.input1", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"50\n"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("cover.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_UNAVAILABLE)
    expect("icon" not in entity_state.attributes).to_be_truthy()

    hass.states.async_set("sensor.input1", "off")
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"25\n"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("cover.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(CoverState.OPEN)
    expect(entity_state.attributes["icon"]).to_equal("mdi:off")


@test
async def icon_template(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test with state value."""
    with tempfile.TemporaryDirectory() as tempdirname:
        path = os.path.join(tempdirname, "cover_status_icon")
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                "command_line": [
                    {
                        "cover": {
                            "command_state": f"cat {path}",
                            "command_open": f"echo 100 > {path}",
                            "command_close": f"echo 0 > {path}",
                            "command_stop": f"echo 0 > {path}",
                            "name": "Test",
                            "icon": '{% if this.attributes.icon=="mdi:icon2" %} mdi:icon1 {% else %} mdi:icon2 {% endif %}',
                        }
                    }
                ]
            },
        )
        await hass.async_block_till_done()
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: "cover.test"},
            blocking=True,
        )

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: "cover.test"},
            blocking=True,
        )
        entity_state = hass.states.get("cover.test")
        expect(entity_state).not_.to_be_none()
        expect(entity_state.attributes.get("icon")).to_equal("mdi:icon1")

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: "cover.test"},
            blocking=True,
        )
        entity_state = hass.states.get("cover.test")
        expect(entity_state).not_.to_be_none()
        expect(entity_state.attributes.get("icon")).to_equal("mdi:icon2")


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
                    "cover": {
                        "command_state": "echo 10",
                        "name": "Test",
                        "value_template": "{{ x - 1 }}",
                        "availability": "{{ value == '50' }}",
                    },
                }
            ]
        },
    )

    error = "Error parsing value for cover.test: 'x' is undefined"
    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"51\n"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(error not in caplog.text).to_be_truthy()

    entity_state = hass.states.get("cover.test")
    expect(entity_state).not_.to_be_none()
    expect(entity_state.state).to_equal(STATE_UNAVAILABLE)

    await hass.async_block_till_done()
    with mock_asyncio_subprocess_run(b"50\n"):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(error in caplog.text).to_be_truthy()
