"""Test the Remote significant change platform."""

from tryke import expect, test

from homeassistant.components.remote import ATTR_ACTIVITY_LIST, ATTR_CURRENT_ACTIVITY
from homeassistant.components.remote.significant_change import (
    async_check_significant_change,
)


@test
async def significant_change() -> None:
    """Detect Remote significant changes."""
    attrs = {
        ATTR_CURRENT_ACTIVITY: "playing",
        ATTR_ACTIVITY_LIST: ["playing", "paused"],
    }
    expect(async_check_significant_change(None, "on", attrs, "on", attrs)).to_be(False)

    expect(async_check_significant_change(None, "on", attrs, "off", attrs)).to_be(True)

    activity_change = {
        "old": {
            ATTR_CURRENT_ACTIVITY: "playing",
            ATTR_ACTIVITY_LIST: ["playing", "paused"],
        },
        "new": {
            ATTR_CURRENT_ACTIVITY: "paused",
            ATTR_ACTIVITY_LIST: ["playing", "paused"],
        },
    }
    expect(
        async_check_significant_change(
            None, "on", activity_change["old"], "on", activity_change["new"]
        )
    ).to_be(True)

    list_only = {
        "old": {
            ATTR_CURRENT_ACTIVITY: "playing",
            ATTR_ACTIVITY_LIST: ["playing", "paused"],
        },
        "new": {
            ATTR_CURRENT_ACTIVITY: "playing",
            ATTR_ACTIVITY_LIST: ["playing"],
        },
    }
    expect(
        async_check_significant_change(
            None, "on", list_only["old"], "on", list_only["new"]
        )
    ).to_be(False)

    unofficial = {
        "old": {
            ATTR_CURRENT_ACTIVITY: "playing",
            ATTR_ACTIVITY_LIST: ["playing", "paused"],
        },
        "new": {
            ATTR_CURRENT_ACTIVITY: "playing",
            ATTR_ACTIVITY_LIST: ["playing", "paused"],
            "not_official": "changed",
        },
    }
    expect(
        async_check_significant_change(
            None, "on", unofficial["old"], "on", unofficial["new"]
        )
    ).to_be(False)
