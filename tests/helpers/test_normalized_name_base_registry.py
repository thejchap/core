"""Tests for the normalized name base registry helper."""

from tryke import Depends, expect, fixture, test

from homeassistant.helpers.normalized_name_base_registry import (
    NormalizedNameBaseRegistryEntry,
    NormalizedNameBaseRegistryItems,
    normalize_name as _normalize_name,
)


@fixture
def _registry_items() -> NormalizedNameBaseRegistryItems:
    """Fixture for registry items."""
    return NormalizedNameBaseRegistryItems[NormalizedNameBaseRegistryEntry]()


@test
def normalize_name() -> None:
    """Test normalize_name."""
    expect(_normalize_name("Hello World")).to_equal("helloworld")
    expect(_normalize_name("HELLO WORLD")).to_equal("helloworld")
    expect(_normalize_name("  Hello   World  ")).to_equal("helloworld")


@test
def registry_items(
    registry_items: NormalizedNameBaseRegistryItems[
        NormalizedNameBaseRegistryEntry
    ] = Depends(_registry_items),
) -> None:
    """Test registry items."""
    entry = NormalizedNameBaseRegistryEntry(name="Hello World")
    registry_items["key"] = entry
    expect(registry_items["key"]).to_equal(entry)
    expect(list(registry_items.values())).to_equal([entry])
    expect(registry_items.get_by_name("Hello World")).to_equal(entry)

    entry2 = NormalizedNameBaseRegistryEntry(name="Hello World 2")
    registry_items["key"] = entry2
    expect(registry_items["key"]).to_equal(entry2)
    expect(list(registry_items.values())).to_equal([entry2])
    expect(registry_items.get_by_name("Hello World 2")).to_equal(entry2)

    del registry_items["key"]
    expect("key" not in registry_items).to_be(True)
    expect(not registry_items.values()).to_be(True)


@test
def key_already_in_use(
    registry_items: NormalizedNameBaseRegistryItems[
        NormalizedNameBaseRegistryEntry
    ] = Depends(_registry_items),
) -> None:
    """Test key already in use."""
    entry = NormalizedNameBaseRegistryEntry(name="Hello World")
    registry_items["key"] = entry

    entry = NormalizedNameBaseRegistryEntry(name="Hello World 2")
    registry_items["key2"] = entry
    expect(lambda: registry_items.__setitem__("key", entry)).to_raise(ValueError)
