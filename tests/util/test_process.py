"""Test process util."""

from functools import partial
import os
import subprocess

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.util import process

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to trigger Tryke's HookExecutor path.

    Tryke only creates a HookExecutor (and therefore only resolves
    Depends() defaults) for modules that statically declare at least
    one @fixture. Consumers of shared fixtures need a local fixture —
    even an unused one — to opt into dependency resolution.
    """
    return 0


@test
async def kill_process(hass: HomeAssistant = Depends(hass)) -> None:
    """Test killing a process."""
    sleeper = await hass.async_add_executor_job(
        partial(
            subprocess.Popen,
            "sleep 1000",
            shell=True,  # noqa: S604
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    )
    pid = sleeper.pid

    expect(os.kill(pid, 0)).to_be(None)

    process.kill_subprocess(sleeper)

    expect(lambda: os.kill(pid, 0)).to_raise(OSError)
