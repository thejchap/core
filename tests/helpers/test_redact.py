"""Test the data redation helper."""

from tryke import expect, test

from homeassistant.helpers.redact import (
    REDACTED,
    async_redact_data,
    partial_redact as _partial_redact,
)


@test
def redact() -> None:
    """Test the async_redact_data helper."""
    data = {
        "key1": "value1",
        "key2": ["value2_a", "value2_b"],
        "key3": [["value_3a", "value_3b"], ["value_3c", "value_3d"]],
        "key4": {
            "key4_1": "value4_1",
            "key4_2": ["value4_2a", "value4_2b"],
            "key4_3": [["value4_3a", "value4_3b"], ["value4_3c", "value4_3d"]],
        },
        "key5": None,
        "key6": "",
        "key7": False,
    }

    to_redact = {
        "key1",
        "key3",
        "key4_1",
        "key5",
        "key6",
        "key7",
    }

    expect(async_redact_data(data, to_redact)).to_equal(
        {
            "key1": REDACTED,
            "key2": ["value2_a", "value2_b"],
            "key3": REDACTED,
            "key4": {
                "key4_1": REDACTED,
                "key4_2": ["value4_2a", "value4_2b"],
                "key4_3": [["value4_3a", "value4_3b"], ["value4_3c", "value4_3d"]],
            },
            "key5": None,
            "key6": "",
            "key7": REDACTED,
        }
    )


@test
def redact_custom_redact_function() -> None:
    """Test the async_redact_data helper."""
    data = {
        "key1": "val1val1val1val1",
        "key2": ["value2_a", "value2_b"],
        "key3": [
            ["val_3avalue_3avalue_3a", "value_3bvalue_3bvalue_3b"],
            ["value_3cvalue_3cvalue_3c", "value_3dvalue_3dvalue_3d"],
        ],
        "key4": {
            "key4_1": "val4_1val4_1val4_1val4_1",
            "key4_2": ["value4_2a", "value4_2b"],
            "key4_3": [["value4_3a", "value4_3b"], ["value4_3c", "value4_3d"]],
        },
        "key5": None,
        "key6": "",
        "key7": False,
    }

    to_redact = {
        "key1": _partial_redact,
        "key3": _partial_redact,  # Value is a list, will default to REDACTED
        "key4_1": _partial_redact,
        "key5": _partial_redact,
        "key6": _partial_redact,
        "key7": _partial_redact,  # Value is False, will default to REDACTED
    }

    expect(async_redact_data(data, to_redact)).to_equal(
        {
            "key1": "val1***val1",
            "key2": ["value2_a", "value2_b"],
            "key3": REDACTED,
            "key4": {
                "key4_1": "val4***l4_1",
                "key4_2": ["value4_2a", "value4_2b"],
                "key4_3": [["value4_3a", "value4_3b"], ["value4_3c", "value4_3d"]],
            },
            "key5": None,
            "key6": "",
            "key7": REDACTED,
        }
    )


@test
def partial_redact() -> None:
    """Test the partial_redact helper."""
    expect(_partial_redact(None, 0, 0)).to_equal(REDACTED)
    expect(_partial_redact("short_string")).to_equal(REDACTED)
    expect(_partial_redact("long_enough_string")).to_equal("long***ring")
    expect(_partial_redact("long_enough_string", 2, 2)).to_equal("lo***ng")
    expect(_partial_redact("long_enough_string", 0, 0)).to_equal(REDACTED)
