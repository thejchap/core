"""Test HassDict and custom HassKey types."""

from tryke import expect, test

from homeassistant.util.hass_dict import HassDict, HassEntryKey, HassKey


@test
def key_comparison() -> None:
    """Test key comparison with itself and string keys."""

    str_key = "custom-key"
    key = HassKey[int](str_key)
    other_key = HassKey[str]("other-key")

    entry_key = HassEntryKey[int](str_key)
    other_entry_key = HassEntryKey[str]("other-key")

    expect(key == str_key).to_be(True)
    expect(key != other_key).to_be(True)
    expect(key != 2).to_be(True)

    expect(entry_key == str_key).to_be(True)
    expect(entry_key != other_entry_key).to_be(True)
    expect(entry_key != 2).to_be(True)

    # Only compare name attribute, HassKey(<name>) == HassEntryKey(<name>)
    expect(key == entry_key).to_be(True)


@test
def hass_dict_access() -> None:
    """Test keys with the same name all access the same value in HassDict."""

    data = HassDict()
    str_key = "custom-key"
    key = HassKey[int](str_key)
    other_key = HassKey[str]("other-key")

    entry_key = HassEntryKey[int](str_key)
    other_entry_key = HassEntryKey[str]("other-key")

    data[str_key] = True
    expect(data.get(key) is True).to_be(True)
    expect(data.get(other_key) is None).to_be(True)

    expect(data.get(entry_key) is True).to_be(True)  # type: ignore[comparison-overlap]
    expect(data.get(other_entry_key) is None).to_be(True)

    data[key] = False
    expect(data[str_key] is False).to_be(True)
