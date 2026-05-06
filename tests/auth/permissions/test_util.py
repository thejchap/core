"""Test the permission utils."""

from tryke import expect, test

from homeassistant.auth.permissions import util


@test
def test_all() -> None:
    """Test if we can test the all group."""
    for val in (None, {}, {"all": None}, {"all": {}}):
        expect(util.test_all(val, "read")).to_be(False)

    for val in (True, {"all": True}, {"all": {"read": True}}):
        expect(util.test_all(val, "read")).to_be(True)
