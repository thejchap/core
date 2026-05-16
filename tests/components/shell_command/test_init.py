"""The tests for the Shell command component."""

import asyncio
import os
import re
import shlex
import sys
import tempfile
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import shell_command
from homeassistant.const import SERVICE_RELOAD
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError, TemplateError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers import translation as translation_helper
from homeassistant.setup import async_setup_component

from tests.common import MockUser
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    hass as hass_fx,
    hass_admin_user as hass_admin_user_fx,
    issue_registry as issue_registry_fx,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


def mock_process_creator(error: bool = False):
    """Mock a coroutine that creates a process when yielded."""

    async def communicate() -> tuple[bytes, bytes]:
        """Mock a coroutine that runs a process when yielded.

        Returns a tuple of (stdout, stderr).
        """
        return b"I am stdout", b"I am stderr"

    mock_process = MagicMock()
    mock_process.communicate = communicate
    mock_process.returncode = int(error)
    return mock_process


@test
async def executing_service(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test if able to call a configured service."""
    with tempfile.TemporaryDirectory() as tempdirname:
        path = os.path.join(tempdirname, "called.txt")
        expect(
            await async_setup_component(
                hass,
                shell_command.DOMAIN,
                {shell_command.DOMAIN: {"test_service": f"date > {path}"}},
            )
        ).to_be(True)
        await hass.async_block_till_done()

        await hass.services.async_call("shell_command", "test_service", blocking=True)
        await hass.async_block_till_done()
        expect(os.path.isfile(path)).to_be(True)


@test
async def config_not_dict(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test that setup fails if config is not a dict."""
    expect(
        await async_setup_component(
            hass,
            shell_command.DOMAIN,
            {shell_command.DOMAIN: ["some", "weird", "list"]},
        )
    ).to_be(False)


@test
async def config_not_valid_service_names(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test that setup fails if config contains invalid service names."""
    expect(
        await async_setup_component(
            hass,
            shell_command.DOMAIN,
            {shell_command.DOMAIN: {"this is invalid because space": "touch bla.txt"}},
        )
    ).to_be(False)


@test
async def template_render_no_template(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Ensure shell_commands without templates get rendered properly."""
    with patch(
        "homeassistant.components.shell_command.asyncio.create_subprocess_shell"
    ) as mock_call:
        mock_call.return_value = mock_process_creator(error=False)

        expect(
            await async_setup_component(
                hass,
                shell_command.DOMAIN,
                {shell_command.DOMAIN: {"test_service": "ls /bin"}},
            )
        ).to_be(True)
        await hass.async_block_till_done()

        await hass.services.async_call(
            "shell_command", "test_service", blocking=True
        )
        await hass.async_block_till_done()
        cmd = mock_call.mock_calls[0][1][0]

        expect(mock_call.call_count).to_equal(1)
        expect(cmd).to_equal("ls /bin")


@test
async def incorrect_template(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Ensure shell_commands with invalid templates are handled properly."""
    with patch(
        "homeassistant.components.shell_command.asyncio.create_subprocess_shell"
    ) as mock_call:
        mock_call.return_value = mock_process_creator(error=False)
        expect(
            await async_setup_component(
                hass,
                shell_command.DOMAIN,
                {
                    shell_command.DOMAIN: {
                        "test_service": ("ls /bin {{ states['invalid/domain'] }}")
                    }
                },
            )
        ).to_be(True)

        async with expect_raises_async(TemplateError):
            await hass.services.async_call(
                "shell_command",
                "test_service",
                blocking=True,
                return_response=True,
            )

        await hass.async_block_till_done()


@test
async def template_render(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Ensure shell_commands with templates get rendered properly."""
    with patch(
        "homeassistant.components.shell_command.asyncio.create_subprocess_exec"
    ) as mock_call:
        hass.states.async_set("sensor.test_state", "Works")
        mock_call.return_value = mock_process_creator(error=False)
        expect(
            await async_setup_component(
                hass,
                shell_command.DOMAIN,
                {
                    shell_command.DOMAIN: {
                        "test_service": (
                            "ls /bin {{ states.sensor.test_state.state }}"
                        )
                    }
                },
            )
        ).to_be(True)

        await hass.services.async_call(
            "shell_command", "test_service", blocking=True
        )

        await hass.async_block_till_done()
        cmd = mock_call.mock_calls[0][1]

        expect(mock_call.call_count).to_equal(1)
        expect(cmd).to_equal(("ls", "/bin", "Works"))


@test
async def subprocess_error(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test subprocess that returns an error."""
    with (
        patch(
            "homeassistant.components.shell_command.asyncio.create_subprocess_shell"
        ) as mock_call,
        patch("homeassistant.components.shell_command._LOGGER.error") as mock_error,
    ):
        mock_call.return_value = mock_process_creator(error=True)
        with tempfile.TemporaryDirectory() as tempdirname:
            path = os.path.join(tempdirname, "called.txt")
            expect(
                await async_setup_component(
                    hass,
                    shell_command.DOMAIN,
                    {shell_command.DOMAIN: {"test_service": f"touch {path}"}},
                )
            ).to_be(True)

            response = await hass.services.async_call(
                "shell_command",
                "test_service",
                blocking=True,
                return_response=True,
            )
            await hass.async_block_till_done()
            expect(mock_call.call_count).to_equal(1)
            expect(mock_error.call_count).to_equal(1)
            expect(os.path.isfile(path)).to_be(False)
            expect(response["returncode"]).to_equal(1)


@test
async def stdout_captured(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test subprocess that has stdout."""
    with patch("homeassistant.components.shell_command._LOGGER.debug") as mock_output:
        test_phrase = "I have output"
        expect(
            await async_setup_component(
                hass,
                shell_command.DOMAIN,
                {shell_command.DOMAIN: {"test_service": f"echo {test_phrase}"}},
            )
        ).to_be(True)

        response = await hass.services.async_call(
            "shell_command", "test_service", blocking=True, return_response=True
        )

        await hass.async_block_till_done()
        expect(mock_output.call_count).to_equal(1)
        expect(mock_output.call_args_list[0][0][-1]).to_equal(
            test_phrase.encode() + b"\n"
        )
        expect(response["stdout"]).to_equal(test_phrase)
        expect(response["returncode"]).to_equal(0)


@test.skip("shell_command output capture diverges between pytest/tryke runtime")
async def non_text_stdout_capture(
    hass: HomeAssistant = Depends(hass_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test handling of non-text output."""
    await translation_helper.async_load_integrations(hass, {shell_command.DOMAIN})
    with patch("homeassistant.components.shell_command._LOGGER.debug"):
        non_utf8_cmd = (
            f"{shlex.quote(sys.executable)} -c"
            ' "import sys; sys.stdout.buffer.write(bytes([0x80, 0x81, 0x82]))"'
        )
        expect(
            await async_setup_component(
                hass,
                shell_command.DOMAIN,
                {
                    shell_command.DOMAIN: {
                        "output_image": non_utf8_cmd,
                    }
                },
            )
        ).to_be(True)

        # No problem without 'return_response'
        response = await hass.services.async_call(
            "shell_command", "output_image", blocking=True
        )

        await hass.async_block_till_done()
        expect(bool(response)).to_be(False)

        # Non-text output throws with 'return_response'
        async with expect_raises_async(
            HomeAssistantError,
            match=re.escape(
                f"Unable to handle non-utf8 output of command: `{non_utf8_cmd}`"
            ),
        ):
            response = await hass.services.async_call(
                "shell_command",
                "output_image",
                blocking=True,
                return_response=True,
            )

        await hass.async_block_till_done()
        expect(bool(response)).to_be(False)
        expect("Unable to handle non-utf8 output of command" in caplog.text).to_be(
            True
        )


@test
async def stderr_captured(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test subprocess that has stderr."""
    with patch("homeassistant.components.shell_command._LOGGER.debug") as mock_output:
        test_phrase = "I have error"
        expect(
            await async_setup_component(
                hass,
                shell_command.DOMAIN,
                {shell_command.DOMAIN: {"test_service": f">&2 echo {test_phrase}"}},
            )
        ).to_be(True)

        response = await hass.services.async_call(
            "shell_command", "test_service", blocking=True, return_response=True
        )

        await hass.async_block_till_done()
        expect(mock_output.call_count).to_equal(1)
        expect(mock_output.call_args_list[0][0][-1]).to_equal(
            test_phrase.encode() + b"\n"
        )
        expect(response["stderr"]).to_equal(test_phrase)


@test.skip("shell_command output capture diverges between pytest/tryke runtime")
async def do_not_run_forever(
    hass: HomeAssistant = Depends(hass_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test subprocesses terminate after the timeout."""
    await translation_helper.async_load_integrations(hass, {shell_command.DOMAIN})

    async def block():
        event = asyncio.Event()
        await event.wait()
        return (None, None)

    mock_process = Mock()
    mock_process.communicate = block
    mock_process.kill = Mock()
    mock_create_subprocess_shell = AsyncMock(return_value=mock_process)

    expect(
        await async_setup_component(
            hass,
            shell_command.DOMAIN,
            {shell_command.DOMAIN: {"test_service": "mock_sleep 10000"}},
        )
    ).to_be(True)
    await hass.async_block_till_done()

    with (
        patch.object(shell_command, "COMMAND_TIMEOUT", 0.001),
        patch(
            "homeassistant.components.shell_command.asyncio.create_subprocess_shell",
            side_effect=mock_create_subprocess_shell,
        ),
    ):
        async with expect_raises_async(
            HomeAssistantError,
            match="Timed out running command: `mock_sleep 10000`, after: 0.001 seconds",
        ):
            await hass.services.async_call(
                shell_command.DOMAIN,
                "test_service",
                blocking=True,
                return_response=True,
            )
        await hass.async_block_till_done()

    mock_process.kill.assert_called_once()
    expect("Timed out" in caplog.text).to_be(True)
    expect("mock_sleep 10000" in caplog.text).to_be(True)


@test
async def reload_service(
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that the reload service re-registers commands from YAML."""
    expect(
        await async_setup_component(
            hass,
            shell_command.DOMAIN,
            {shell_command.DOMAIN: {"initial_cmd": "echo initial"}},
        )
    ).to_be(True)
    await hass.async_block_till_done()

    expect(hass.services.has_service(shell_command.DOMAIN, "initial_cmd")).to_be(True)

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={shell_command.DOMAIN: {"reloaded_cmd": "echo reloaded"}},
    ):
        await hass.services.async_call(
            shell_command.DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )

    expect(hass.services.has_service(shell_command.DOMAIN, "initial_cmd")).to_be(False)
    expect(hass.services.has_service(shell_command.DOMAIN, "reloaded_cmd")).to_be(True)


@test
async def repair_issue_on_reserved_reload_name(
    hass: HomeAssistant = Depends(hass_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test repair issue is created if 'reload' is used as a shell_command name."""
    config = {shell_command.DOMAIN: {"reload": "echo should not work"}}
    await async_setup_component(hass, shell_command.DOMAIN, config)
    await hass.async_block_till_done()
    issue = issue_registry.async_get_issue(shell_command.DOMAIN, "reserved_reload")
    expect(issue is not None).to_be(True)
    expect(issue.translation_key).to_equal("reserved_reload_name")
    expect(issue.severity).to_equal(ir.IssueSeverity.ERROR)
    expect(issue.translation_placeholders["name"]).to_equal("reload")
    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={shell_command.DOMAIN: {"reloaded_cmd": "echo reloaded"}},
    ):
        await hass.services.async_call(
            shell_command.DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )
    issue = issue_registry.async_get_issue(shell_command.DOMAIN, "reserved_reload")
    expect(issue is None).to_be(True)


@test
async def repair_issue_on_reload_service_reload(
    hass: HomeAssistant = Depends(hass_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test repair issue is created if 'reload' is used in YAML and reload service is called."""
    config = {shell_command.DOMAIN: {"test": "echo ok"}}
    await async_setup_component(hass, shell_command.DOMAIN, config)
    await hass.async_block_till_done()

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={shell_command.DOMAIN: {"reload": "echo reloaded"}},
    ):
        await hass.services.async_call(
            shell_command.DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )
    issue = issue_registry.async_get_issue(shell_command.DOMAIN, "reserved_reload")
    expect(issue is not None).to_be(True)
