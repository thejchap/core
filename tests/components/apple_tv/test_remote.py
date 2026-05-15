"""Test apple_tv remote."""

from unittest.mock import AsyncMock

from tryke import expect, test

from homeassistant.components.apple_tv.remote import AppleTVRemote
from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_HOLD_SECS,
    ATTR_NUM_REPEATS,
)


@test.cases(
    test.case("up", command="up", method="remote_control.up", hold_secs=0.0),
    test.case("wakeup", command="wakeup", method="power.turn_on", hold_secs=0.0),
    test.case(
        "volume_up", command="volume_up", method="audio.volume_up", hold_secs=0.0
    ),
)
async def send_command_short_press(
    *, command: str, method: str, hold_secs: float
) -> None:
    """Test "send_command" method without hold."""
    remote = AppleTVRemote("test", "test", None)
    remote.atv = AsyncMock()
    await remote.async_send_command(
        [command],
        **{ATTR_NUM_REPEATS: 1, ATTR_DELAY_SECS: 0, ATTR_HOLD_SECS: hold_secs},
    )
    expect(len(remote.atv.method_calls)).to_equal(1)
    expect(str(remote.atv.method_calls[0])).to_equal(f"call.{method}()")


@test.cases(
    test.case("home", command="home", method="remote_control.home", hold_secs=1.0),
    test.case(
        "select", command="select", method="remote_control.select", hold_secs=1.0
    ),
)
async def send_command_hold(*, command: str, method: str, hold_secs: float) -> None:
    """Test "send_command" method with hold."""
    remote = AppleTVRemote("test", "test", None)
    remote.atv = AsyncMock()
    await remote.async_send_command(
        [command],
        **{ATTR_NUM_REPEATS: 1, ATTR_DELAY_SECS: 0, ATTR_HOLD_SECS: hold_secs},
    )
    expect(len(remote.atv.method_calls)).to_equal(1)
    expect(str(remote.atv.method_calls[0])).to_equal(
        f"call.{method}(action=<InputAction.Hold: 2>)"
    )
