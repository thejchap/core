"""Test read only dictionary."""

import copy
import json

from tryke import expect, test

from homeassistant.util.read_only_dict import ReadOnlyDict


@test
def read_only_dict() -> None:
    """Test read only dictionary."""
    data = ReadOnlyDict({"hello": "world"})

    def set_existing() -> None:
        data["hello"] = "universe"

    def set_new() -> None:
        data["other_key"] = "universe"

    expect(set_existing).to_raise(RuntimeError)
    expect(set_new).to_raise(RuntimeError)
    expect(lambda: data.pop("hello")).to_raise(RuntimeError)
    expect(lambda: data.popitem()).to_raise(RuntimeError)
    expect(lambda: data.clear()).to_raise(RuntimeError)
    expect(lambda: data.update({"yo": "yo"})).to_raise(RuntimeError)
    expect(lambda: data.setdefault("yo", "yo")).to_raise(RuntimeError)

    expect(isinstance(data, dict)).to_be(True)
    expect(dict(data)).to_equal({"hello": "world"})
    expect(json.dumps(data)).to_equal(json.dumps({"hello": "world"}))

    expect(copy.deepcopy(data)).to_equal({"hello": "world"})
