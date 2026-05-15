"""Test Teltonika utility helpers."""

from tryke import expect, test

from homeassistant.components.teltonika.util import get_url_variants, normalize_url


@test
def normalize_url_adds_https_scheme() -> None:
    """Test normalize_url adds HTTPS scheme for bare hostnames."""
    expect(normalize_url("teltonika")).to_equal("https://teltonika")


@test
def normalize_url_preserves_scheme() -> None:
    """Test normalize_url preserves explicitly provided scheme."""
    expect(normalize_url("http://teltonika")).to_equal("http://teltonika")
    expect(normalize_url("https://teltonika")).to_equal("https://teltonika")


@test
def normalize_url_strips_path() -> None:
    """Test normalize_url removes any path component."""
    expect(normalize_url("https://teltonika/api")).to_equal("https://teltonika")
    expect(normalize_url("http://teltonika/other/path")).to_equal("http://teltonika")


@test
def get_url_variants_with_https_scheme() -> None:
    """Test get_url_variants with explicit HTTPS scheme returns only HTTPS."""
    expect(get_url_variants("https://teltonika")).to_equal(["https://teltonika"])


@test
def get_url_variants_with_http_scheme() -> None:
    """Test get_url_variants with explicit HTTP scheme returns only HTTP."""
    expect(get_url_variants("http://teltonika")).to_equal(["http://teltonika"])


@test
def get_url_variants_without_scheme() -> None:
    """Test get_url_variants without scheme returns both HTTPS and HTTP."""
    expect(get_url_variants("teltonika")).to_equal(
        ["https://teltonika", "http://teltonika"]
    )
