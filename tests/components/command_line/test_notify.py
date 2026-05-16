"""The tests for the command line notification platform."""

import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.components.command_line import DOMAIN
from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from ._fixtures import async_load_yaml_integration

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
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
        "notify",
        {
            "notify": {
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
        DOMAIN, "notify_platform_yaml_not_supported"
    )
    expect(issue).not_.to_be_none()
    expect(issue.severity).to_equal(ir.IssueSeverity.ERROR)
    expect(issue.translation_placeholders).to_equal({"platform": NOTIFY_DOMAIN})


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
                    "notify": {
                        "command": "exit 0",
                        "name": "Test2",
                    }
                }
            ]
        },
    )
    expect(hass.services.has_service(NOTIFY_DOMAIN, "test2")).to_be_truthy()


@test
async def bad_config(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set up the platform with bad/missing configuration."""
    expect(
        await setup.async_setup_component(
            hass,
            NOTIFY_DOMAIN,
            {
                NOTIFY_DOMAIN: [
                    {"platform": "command_line"},
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(hass.services.has_service(NOTIFY_DOMAIN, "test")).to_be_falsy()


@test
async def command_line_output(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the command line output."""
    with tempfile.TemporaryDirectory() as tempdirname:
        filename = os.path.join(tempdirname, "message.txt")
        message = "one, two, testing, testing"
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                "command_line": [
                    {
                        "notify": {
                            "command": f"cat > {filename}",
                            "name": "Test3",
                        }
                    }
                ]
            },
        )
        await hass.async_block_till_done()

        expect(hass.services.has_service(NOTIFY_DOMAIN, "test3")).to_be_truthy()

        await hass.services.async_call(
            NOTIFY_DOMAIN, "test3", {"message": message}, blocking=True
        )
        expect(
            await hass.async_add_executor_job(Path(filename).read_text)
        ).to_equal(message)


@test
async def command_line_output_single_command(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the command line output."""

    await setup.async_setup_component(
        hass,
        DOMAIN,
        {
            "command_line": [
                {
                    "notify": {
                        "command": "echo",
                        "name": "Test3",
                    }
                }
            ]
        },
    )
    await hass.async_block_till_done()

    expect(hass.services.has_service(NOTIFY_DOMAIN, "test3")).to_be_truthy()

    await hass.services.async_call(
        NOTIFY_DOMAIN, "test3", {"message": "test message"}, blocking=True
    )
    expect("Running command: echo" in caplog.text).to_be_truthy()
    expect("Running with message: test message" in caplog.text).to_be_truthy()


@test
async def command_template(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test the command line output using template as command."""

    with tempfile.TemporaryDirectory() as tempdirname:
        filename = os.path.join(tempdirname, "message.txt")
        message = "one, two, testing, testing"
        hass.states.async_set("sensor.test_state", filename)
        await setup.async_setup_component(
            hass,
            DOMAIN,
            {
                "command_line": [
                    {
                        "notify": {
                            "command": "cat > {{ states.sensor.test_state.state }}",
                            "name": "Test3",
                        }
                    }
                ]
            },
        )
        await hass.async_block_till_done()

        expect(hass.services.has_service(NOTIFY_DOMAIN, "test3")).to_be_truthy()

        await hass.services.async_call(
            NOTIFY_DOMAIN, "test3", {"message": message}, blocking=True
        )
        expect(
            await hass.async_add_executor_job(Path(filename).read_text)
        ).to_equal(message)


@test
async def command_incorrect_template(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the command line output using template as command which isn't working."""

    message = "one, two, testing, testing"
    await setup.async_setup_component(
        hass,
        DOMAIN,
        {
            "command_line": [
                {
                    "notify": {
                        "command": "cat > {{ this template doesn't parse ",
                        "name": "Test3",
                    }
                }
            ]
        },
    )
    await hass.async_block_till_done()

    expect(hass.services.has_service(NOTIFY_DOMAIN, "test3")).to_be_truthy()

    await hass.services.async_call(
        NOTIFY_DOMAIN, "test3", {"message": message}, blocking=True
    )

    expect(
        "Error rendering command template: TemplateSyntaxError: expected token"
        in caplog.text
    ).to_be_truthy()


@test
async def error_for_none_zero_exit_code(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test if an error is logged for non zero exit codes."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "notify": {
                        "command": "exit 1",
                        "name": "Test4",
                    }
                }
            ]
        },
    )

    await hass.services.async_call(
        NOTIFY_DOMAIN, "test4", {"message": "error"}, blocking=True
    )
    expect("Command failed" in caplog.text).to_be_truthy()
    expect("return code 1" in caplog.text).to_be_truthy()


@test
async def timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test blocking is not forever."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "notify": {
                        "command": "sleep 10000",
                        "command_timeout": 0.0000001,
                        "name": "Test5",
                    }
                }
            ]
        },
    )
    await hass.services.async_call(
        NOTIFY_DOMAIN, "test5", {"message": "error"}, blocking=True
    )
    expect("Timeout" in caplog.text).to_be_truthy()


@test
async def subprocess_exceptions(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that notify subprocess exceptions are handled correctly."""
    await async_load_yaml_integration(
        hass,
        {
            "command_line": [
                {
                    "notify": {
                        "command": "exit 0",
                        "name": "Test6",
                    }
                }
            ]
        },
    )

    with patch(
        "homeassistant.components.command_line.notify.subprocess.Popen"
    ) as check_output:
        check_output.return_value.__enter__ = check_output
        check_output.return_value.communicate.side_effect = [
            subprocess.TimeoutExpired("cmd", 10),
            None,
            subprocess.SubprocessError(),
        ]

        await hass.services.async_call(
            NOTIFY_DOMAIN, "test6", {"message": "error"}, blocking=True
        )
        expect(check_output.call_count).to_equal(2)
        expect("Timeout for command" in caplog.text).to_be_truthy()

        await hass.services.async_call(
            NOTIFY_DOMAIN, "test6", {"message": "error"}, blocking=True
        )
        expect(check_output.call_count).to_equal(4)
        expect("Error trying to exec command" in caplog.text).to_be_truthy()
