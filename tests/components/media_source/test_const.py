"""Test constants for the media source component."""

from tryke import expect, test

from homeassistant.components.media_source.const import URI_SCHEME_REGEX


@test.cases(
    test.case("scheme_only", uri="media-source://", expected_domain=None, expected_identifier=None),
    test.case(
        "domain_only",
        uri="media-source://local_media",
        expected_domain="local_media",
        expected_identifier=None,
    ),
    test.case(
        "domain_path",
        uri="media-source://local_media/some/path/file.mp3",
        expected_domain="local_media",
        expected_identifier="some/path/file.mp3",
    ),
    test.case("a_b", uri="media-source://a/b", expected_domain="a", expected_identifier="b"),
    test.case(
        "spaces",
        uri="media-source://domain/file with spaces.mp4",
        expected_domain="domain",
        expected_identifier="file with spaces.mp4",
    ),
    test.case(
        "dashes",
        uri="media-source://domain/file-with-dashes.mp3",
        expected_domain="domain",
        expected_identifier="file-with-dashes.mp3",
    ),
    test.case(
        "dots",
        uri="media-source://domain/file.with.dots.mp3",
        expected_domain="domain",
        expected_identifier="file.with.dots.mp3",
    ),
    test.case(
        "specials",
        uri="media-source://domain/special!@#$%^&*()chars",
        expected_domain="domain",
        expected_identifier="special!@#$%^&*()chars",
    ),
)
def valid_uri_patterns(
    uri: str, expected_domain: str | None, expected_identifier: str | None
) -> None:
    """Test various valid URI patterns."""
    match = URI_SCHEME_REGEX.match(uri)
    expect(match is not None).to_be(True)
    expect(match.group("domain")).to_equal(expected_domain)
    expect(match.group("identifier")).to_equal(expected_identifier)


@test.cases(
    test.case("missing_double_slash", uri="media-source:"),
    test.case("missing_second_slash", uri="media-source:/"),
    test.case("extra_slash", uri="media-source:///"),
    test.case("trailing_slash", uri="media-source://domain/"),
    test.case("wrong_scheme", uri="invalid-scheme://domain"),
    test.case("missing_colon", uri="media-source//domain"),
    test.case("uppercase_scheme", uri="MEDIA-SOURCE://domain"),
    test.case("underscore_scheme", uri="media_source://domain"),
    test.case("empty", uri=""),
    test.case("scheme_only_no_slashes", uri="media-source"),
    test.case("extra_content", uri="media-source://domain extra"),
    test.case("prefix_content", uri="prefix media-source://domain"),
    test.case("suffix_content", uri="media-source://domain suffix"),
    test.case("leading_underscore", uri="media-source://_test"),
    test.case("trailing_underscore", uri="media-source://test_"),
    test.case("surrounding_underscores", uri="media-source://_test_"),
    test.case("single_underscore", uri="media-source://_"),
    test.case("hyphen", uri="media-source://test-123"),
    test.case("dot", uri="media-source://test.123"),
    test.case("space", uri="media-source://test 123"),
    test.case("all_caps", uri="media-source://TEST"),
    test.case("mixed_case", uri="media-source://Test"),
    test.case("identifier_starts_slash", uri="media-source://domain//invalid"),
)
def invalid_uris(uri: str) -> None:
    """Test invalid URI formats."""
    match = URI_SCHEME_REGEX.match(uri)
    expect(match is None).to_be(True)
