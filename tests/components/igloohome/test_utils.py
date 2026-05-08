"""Test functions in utils module."""

from tryke import expect, test

from homeassistant.components.igloohome.utils import get_linked_bridge

from ._fixtures import (
    GET_DEVICE_INFO_RESPONSE_BRIDGE_LINKED_LOCK,
    GET_DEVICE_INFO_RESPONSE_BRIDGE_NO_LINKED_DEVICE,
    GET_DEVICE_INFO_RESPONSE_LOCK,
)


@test
def get_linked_bridge_expect_bridge_id_returned() -> None:
    """Test that get_linked_bridge returns the bridge ID."""
    expect(
        get_linked_bridge(
            GET_DEVICE_INFO_RESPONSE_LOCK.deviceId,
            [GET_DEVICE_INFO_RESPONSE_BRIDGE_LINKED_LOCK],
        )
    ).to_equal(GET_DEVICE_INFO_RESPONSE_BRIDGE_LINKED_LOCK.deviceId)


@test
def get_linked_bridge_expect_none_returned() -> None:
    """Test that get_linked_bridge returns None."""
    expect(
        get_linked_bridge(
            GET_DEVICE_INFO_RESPONSE_LOCK.deviceId,
            [GET_DEVICE_INFO_RESPONSE_BRIDGE_NO_LINKED_DEVICE],
        )
    ).to_be(None)
