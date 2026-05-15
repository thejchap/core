"""Test Media Source initialization."""

from tryke import expect, test

from homeassistant.components import media_source


@test
async def is_media_source_id() -> None:
    """Test media source validation."""
    expect(media_source.is_media_source_id(media_source.URI_SCHEME)).to_be_truthy()
    expect(
        media_source.is_media_source_id(f"{media_source.URI_SCHEME}domain")
    ).to_be_truthy()
    expect(
        media_source.is_media_source_id(
            f"{media_source.URI_SCHEME}domain/identifier"
        )
    ).to_be_truthy()
    expect(media_source.is_media_source_id("test")).to_be_falsy()


@test
async def generate_media_source_id() -> None:
    """Test identifier generation."""
    tests = [
        (None, None),
        (None, ""),
        ("", ""),
        ("domain", None),
        ("domain", ""),
        ("domain", "identifier"),
    ]

    for domain, identifier in tests:
        expect(
            media_source.is_media_source_id(
                media_source.generate_media_source_id(domain, identifier)
            )
        ).to_be_truthy()
