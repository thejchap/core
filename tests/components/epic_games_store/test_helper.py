"""Tests for the Epic Games Store helpers."""

from typing import Any

from tryke import expect, test

from homeassistant.components.epic_games_store.helper import (
    format_game_data,
    get_game_url,
    is_free_game,
)

from .const import (
    DATA_ERROR_ATTRIBUTE_NOT_FOUND,
    DATA_FREE_GAMES_MYSTERY_SPECIAL,
    DATA_FREE_GAMES_ONE,
)

_FREE_DISCOUNT_TRUE = DATA_FREE_GAMES_ONE["data"]["Catalog"]["searchStore"][
    "elements"
][2]
_FREE_DISCOUNT_FALSE = DATA_FREE_GAMES_ONE["data"]["Catalog"]["searchStore"][
    "elements"
][0]
_ATTR_NOT_FOUND_1 = DATA_ERROR_ATTRIBUTE_NOT_FOUND["data"]["Catalog"]["searchStore"][
    "elements"
][1]
_ATTR_NOT_FOUND_4 = DATA_ERROR_ATTRIBUTE_NOT_FOUND["data"]["Catalog"]["searchStore"][
    "elements"
][4]
_ATTR_NOT_FOUND_5 = DATA_ERROR_ATTRIBUTE_NOT_FOUND["data"]["Catalog"]["searchStore"][
    "elements"
][5]
_MYSTERY_SPECIAL_2 = DATA_FREE_GAMES_MYSTERY_SPECIAL["data"]["Catalog"]["searchStore"][
    "elements"
][2]


@test
def format_game_data_test() -> None:
    """Test game data format."""
    game_data = format_game_data(_FREE_DISCOUNT_TRUE, "fr")
    expect(game_data).not_.to_be_none()
    expect(game_data["title"]).not_.to_be_none()
    expect(game_data["description"]).not_.to_be_none()
    expect(game_data["released_at"]).not_.to_be_none()
    expect(game_data["original_price"]).not_.to_be_none()
    expect(game_data["publisher"]).not_.to_be_none()
    expect(game_data["url"]).not_.to_be_none()
    expect(game_data["img_portrait"]).not_.to_be_none()
    expect(game_data["img_landscape"]).not_.to_be_none()
    expect(game_data["discount_type"]).to_equal("free")
    expect(game_data["discount_start_at"]).not_.to_be_none()
    expect(game_data["discount_end_at"]).not_.to_be_none()


@test.cases(
    test.case("destiny2", raw_game_data=_ATTR_NOT_FOUND_1, expected_result="/p/destiny-2--bungie-30th-anniversary-pack"),
    test.case("qube_bundle", raw_game_data=_ATTR_NOT_FOUND_4, expected_result="/bundles/qube-ultimate-bundle"),
    test.case("payday2", raw_game_data=_ATTR_NOT_FOUND_5, expected_result="/p/payday-2-c66369"),
    test.case("farming_sim", raw_game_data=_MYSTERY_SPECIAL_2, expected_result="/p/farming-simulator-22"),
)
def get_game_url_test(raw_game_data: dict[str, Any], expected_result: str) -> None:
    """Test to get the game URL."""
    expect(get_game_url(raw_game_data, "fr").endswith(expected_result)).to_be(True)


@test.cases(
    test.case("free_discount_true", raw_game_data=_FREE_DISCOUNT_TRUE, expected_result=True),
    test.case("free_discount_false", raw_game_data=_FREE_DISCOUNT_FALSE, expected_result=False),
    test.case("attr_not_found_1", raw_game_data=_ATTR_NOT_FOUND_1, expected_result=False),
    test.case("mystery_special_2", raw_game_data=_MYSTERY_SPECIAL_2, expected_result=True),
)
def is_free_game_test(raw_game_data: dict[str, Any], expected_result: bool) -> None:
    """Test if this game is free."""
    expect(is_free_game(raw_game_data)).to_equal(expected_result)
