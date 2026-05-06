"""Test EventType implementation."""

from __future__ import annotations

import orjson

from tryke import expect, test

from homeassistant.util.event_type import EventType


@test
def compatibility_with_str() -> None:
    """Test EventType. At runtime it should be (almost) fully compatible with str."""

    event = EventType("Hello World")
    expect(event).to_equal("Hello World")
    expect(len(event)).to_equal(11)
    expect(hash(event)).to_equal(hash("Hello World"))
    d: dict[str | EventType, int] = {EventType("key"): 2}
    expect(d["key"]).to_equal(2)


@test
def json_dump() -> None:
    """Test EventType json dump with orjson."""

    event = EventType("state_changed")
    expect(orjson.dumps({"event_type": event})).to_equal(b'{"event_type":"state_changed"}')
