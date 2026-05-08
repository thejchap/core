"""Test for utility functions of the Bring! integration."""

from bring_api import BringItemsResponse, BringListResponse, BringUserSettingsResponse
from tryke import expect, test

from homeassistant.components.bring.const import DOMAIN
from homeassistant.components.bring.coordinator import BringData
from homeassistant.components.bring.util import list_language, sum_attributes

from tests.common import load_fixture


@test.cases(
    test.case("german_list", list_uuid="e542eef6-dba7-4c31-a52c-29e6ab9d83a5", expected="de-DE"),
    test.case("english_list", list_uuid="b4776778-7f6c-496e-951b-92a35d3db0dd", expected="en-US"),
    test.case("unknown_list", list_uuid="00000000-0000-0000-0000-000000000000", expected=None),
)
def list_language_test(*, list_uuid: str, expected: str | None) -> None:
    """Test function list_language."""
    result = list_language(
        list_uuid,
        BringUserSettingsResponse.from_json(load_fixture("usersettings.json", DOMAIN)),
    )
    expect(result).to_equal(expected)


@test.cases(
    test.case("urgent", attribute="urgent", expected=2),
    test.case("convenient", attribute="convenient", expected=2),
    test.case("discounted", attribute="discounted", expected=2),
)
def sum_attributes_test(*, attribute: str, expected: int) -> None:
    """Test function sum_attributes."""
    items = BringItemsResponse.from_json(load_fixture("items.json", DOMAIN))
    lst = BringListResponse.from_json(load_fixture("lists.json", DOMAIN))
    result = sum_attributes(
        BringData(lst.lists[0], items),
        attribute,
    )
    expect(result).to_equal(expected)
