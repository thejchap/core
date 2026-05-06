"""Test Home Assistant uuid util methods."""

import uuid

from tryke import expect, test

from homeassistant.util import uuid as uuid_util


@test
async def uuid_util_random_uuid_hex() -> None:
    """Verify we can generate a random uuid."""
    expect(len(uuid_util.random_uuid_hex())).to_equal(32)
    expect(lambda: uuid.UUID(uuid_util.random_uuid_hex())).not_.to_raise()
