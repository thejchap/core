"""Test Home Assistant ulid util methods."""

import uuid

from tryke import expect, test

from homeassistant.util import ulid as ulid_util


@test
async def ulid_util_uuid_hex() -> None:
    """Verify we can generate a ulid in hex."""
    expect(len(ulid_util.ulid_hex())).to_equal(32)
    expect(lambda: uuid.UUID(ulid_util.ulid_hex())).not_.to_raise()


@test
async def ulid_util_uuid() -> None:
    """Verify we can generate a ulid."""
    expect(len(ulid_util.ulid())).to_equal(26)
