"""Test Home Assistant language util methods."""

from __future__ import annotations

from tryke import expect, test

from homeassistant.const import MATCH_ALL
from homeassistant.util import language


@test
def match_all() -> None:
    """Test MATCH_ALL."""
    expect(language.matches(MATCH_ALL, ["fr-Fr", "en-US", "en-GB"])).to_equal(
        ["fr-Fr", "en-US", "en-GB"]
    )


@test
def region_match() -> None:
    """Test that an exact language/region match is preferred."""
    expect(language.matches("en-GB", ["fr-Fr", "en-US", "en-GB"])).to_equal(
        ["en-GB", "en-US"]
    )


@test
def no_match() -> None:
    """Test that an empty list is returned when there is no match."""
    expect(language.matches("en-US", ["de-DE", "fr-FR", "zh"])).to_equal([])
    expect(language.matches("en", ["de-DE", "fr-FR", "zh"])).to_equal([])
    expect(language.matches("en", [])).to_equal([])


@test
def prefer_us_english() -> None:
    """Test that U.S. English is preferred when no region is provided."""
    expect(language.matches("en", ["en-GB", "en-US", "fr-FR"])).to_equal(
        ["en-US", "en-GB"]
    )


@test
def country_preferred() -> None:
    """Test that country hint disambiguates."""
    expect(language.matches("en", ["fr-Fr", "en-US", "en-GB"], country="GB")).to_equal(
        ["en-GB", "en-US"]
    )


@test
def country_preferred_over_family() -> None:
    """Test that country hint is preferred over language family."""
    expect(language.matches("de", ["de", "de-CH", "de-DE"], country="CH")[0]).to_equal(
        "de-CH"
    )
    expect(language.matches("de", ["de", "de-CH", "de-DE"], country="DE")[0]).to_equal(
        "de-DE"
    )


@test
def language_as_region() -> None:
    """Test that the language itself can be interpreted as a region."""
    expect(language.matches("fr", ["en-US", "en-GB", "fr-CA", "fr-FR"])).to_equal(
        ["fr-FR", "fr-CA"]
    )


@test
def zh_hant() -> None:
    """Test that the zh-Hant matches HK or TW."""
    expect(language.matches("zh-Hant", ["en-US", "en-GB", "zh-CN", "zh-HK"])).to_equal(
        ["zh-HK", "zh-CN"]
    )

    expect(language.matches("zh-Hant", ["en-US", "en-GB", "zh-CN", "zh-TW"])).to_equal(
        ["zh-TW", "zh-CN"]
    )


@test.cases(
    test.case("zh-Hant", target="zh-Hant"),
    test.case("zh-Hans", target="zh-Hans"),
)
def zh_with_country(target: str) -> None:
    """Test that the zh-Hant/zh-Hans still matches country when provided."""
    supported = ["en-US", "en-GB", "zh-CN", "zh-HK", "zh-TW"]
    expect(language.matches(target, supported, country="TW")[0]).to_equal("zh-TW")
    expect(language.matches(target, supported, country="HK")[0]).to_equal("zh-HK")
    expect(language.matches(target, supported, country="CN")[0]).to_equal("zh-CN")


@test
def zh_hans() -> None:
    """Test that the zh-Hans matches CN first."""
    expect(
        language.matches("zh-Hans", ["en-US", "en-GB", "zh-CN", "zh-HK", "zh-TW"])
    ).to_equal(["zh-CN", "zh-HK", "zh-TW"])


@test
def zh_no_code() -> None:
    """Test that the zh defaults to CN first."""
    expect(
        language.matches("zh", ["en-US", "en-GB", "zh-CN", "zh-HK", "zh-TW"])
    ).to_equal(["zh-CN", "zh-HK", "zh-TW"])


@test
def es_419() -> None:
    """Test that the es-419 matches es dialects."""
    expect(
        language.matches("es-419", ["en-US", "en-GB", "es-CL", "es-US", "es-ES"])
    ).to_equal(["es-ES", "es-CL", "es-US"])


@test
def sr_latn() -> None:
    """Test that the sr_Latn matches sr dialects."""
    expect(language.matches("sr-Latn", ["en-US", "en-GB", "sr-CS", "sr-RS"])).to_equal(
        ["sr-CS", "sr-RS"]
    )

    # Prefer exact match with code.
    expect(language.matches("sr", ["sr-Latn", "sr"])).to_equal(["sr", "sr-Latn"])


@test
def no_nb_same() -> None:
    """Test that the no/nb are interchangeable."""
    expect(language.matches("no", ["en-US", "en-GB", "nb"])).to_equal(["nb"])
    expect(language.matches("nb", ["en-US", "en-GB", "no"])).to_equal(["no"])


@test
def no_nb_prefer_exact() -> None:
    """Test that the exact language is preferred even if an interchangeable language is available."""
    expect(language.matches("no", ["en-US", "en-GB", "nb", "no"])).to_equal(
        ["no", "nb"]
    )
    expect(language.matches("no", ["en-US", "en-GB", "no", "nb"])).to_equal(
        ["no", "nb"]
    )


@test
def no_nb_prefer_exact_regions() -> None:
    """Test that the exact language/region is preferred."""
    expect(language.matches("no-AA", ["en-US", "en-GB", "nb-AA", "no-AA"])).to_equal(
        ["no-AA", "nb-AA"]
    )
    expect(language.matches("no-AA", ["en-US", "en-GB", "no-AA", "nb-AA"])).to_equal(
        ["no-AA", "nb-AA"]
    )


@test
def he_iw_same() -> None:
    """Test that the he/iw are interchangeable."""
    expect(language.matches("he", ["en-US", "en-GB", "iw"])).to_equal(["iw"])
    expect(language.matches("iw", ["en-US", "en-GB", "he"])).to_equal(["he"])


@test
def he_iw_prefer_exact() -> None:
    """Test that the exact language is preferred even if an interchangeable language is available."""
    expect(language.matches("he", ["en-US", "en-GB", "iw", "he"])).to_equal(
        ["he", "iw"]
    )
    expect(language.matches("he", ["en-US", "en-GB", "he", "iw"])).to_equal(
        ["he", "iw"]
    )


@test
def he_iw_prefer_exact_regions() -> None:
    """Test that the exact language/region is preferred."""
    expect(language.matches("he-IL", ["en-US", "en-GB", "iw-IL", "he-IL"])).to_equal(
        ["he-IL", "iw-IL"]
    )
    expect(language.matches("he-IL", ["en-US", "en-GB", "he-IL", "iw-IL"])).to_equal(
        ["he-IL", "iw-IL"]
    )
