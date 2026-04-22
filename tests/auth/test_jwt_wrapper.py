"""Tests for the Home Assistant auth jwt_wrapper module."""

import jwt
from tryke import expect, test

from homeassistant.auth import jwt_wrapper


@test
async def reject_access_token_with_impossible_large_size() -> None:
    """Test rejecting access tokens with impossible sizes."""
    expect(
        lambda: jwt_wrapper.unverified_hs256_token_decode("a" * 10000)
    ).to_raise(jwt.DecodeError)
