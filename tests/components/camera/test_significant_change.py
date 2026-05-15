"""Test the Camera significant change platform."""

from tryke import expect, test

from homeassistant.components.camera import CameraState
from homeassistant.components.camera.significant_change import (
    async_check_significant_change,
)


@test
async def significant_change() -> None:
    """Detect Camera significant changes."""
    attrs: dict = {}
    expect(
        async_check_significant_change(
            None, CameraState.IDLE, attrs, CameraState.IDLE, attrs
        )
    ).to_be_falsy()
    expect(
        async_check_significant_change(
            None, CameraState.IDLE, attrs, CameraState.IDLE, {"dummy": "dummy"}
        )
    ).to_be_falsy()
    expect(
        async_check_significant_change(
            None, CameraState.IDLE, attrs, CameraState.RECORDING, attrs
        )
    ).to_be_truthy()
