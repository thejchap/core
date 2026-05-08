"""Test Cloudflare integration helpers."""

from tryke import expect, test

from homeassistant.components.cloudflare.helpers import get_zone_id


@test
def get_zone_id_test() -> None:
    """Test get_zone_id."""
    zones = [
        {"id": "1", "name": "example.com"},
        {"id": "2", "name": "example.org"},
    ]
    expect(get_zone_id("example.com", zones)).to_equal("1")
    expect(get_zone_id("example.org", zones)).to_equal("2")
    expect(get_zone_id("example.net", zones)).to_be(None)
