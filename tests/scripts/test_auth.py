"""Test the auth script to manage local users."""

import argparse
import asyncio
import contextlib
import io
import logging
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.auth.providers import homeassistant as hass_auth
from homeassistant.core import HomeAssistant
from homeassistant.scripts import auth as script_auth

from tests.common import register_auth_provider
from tests.hass_fixtures import hass, hass_storage


@contextlib.contextmanager
def _reset_log_level():
    """Reset the homeassistant.core log level around a block."""
    logger = logging.getLogger("homeassistant.core")
    orig_level = logger.level
    try:
        yield
    finally:
        logger.setLevel(orig_level)


@fixture
async def provider(hass: HomeAssistant = Depends(hass)) -> hass_auth.HassAuthProvider:
    """Home Assistant auth provider."""
    provider = await register_auth_provider(hass, {"type": "homeassistant"})
    await provider.async_initialize()
    return provider


@test
async def list_user(
    hass: HomeAssistant = Depends(hass),
    provider: hass_auth.HassAuthProvider = Depends(provider),
) -> None:
    """Test we can list users."""
    with _reset_log_level():
        data = provider.data
        data.add_auth("test-user", "test-pass")
        data.add_auth("second-user", "second-pass")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            await script_auth.list_users(hass, provider, None)

        expect(buf.getvalue()).to_equal(
            "test-user\nsecond-user\n\nTotal users: 2\n"
        )


@test
async def add_user(
    hass: HomeAssistant = Depends(hass),
    provider: hass_auth.HassAuthProvider = Depends(provider),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test we can add a user."""
    with _reset_log_level():
        data = provider.data
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            await script_auth.add_user(
                hass, provider, Mock(username="paulus", password="test-pass")
            )

        expect(len(hass_storage[hass_auth.STORAGE_KEY]["data"]["users"])).to_equal(1)
        expect(buf.getvalue()).to_equal("Auth created\n")

        expect(len(data.users)).to_equal(1)
        data.validate_login("paulus", "test-pass")


@test
async def validate_login(
    hass: HomeAssistant = Depends(hass),
    provider: hass_auth.HassAuthProvider = Depends(provider),
) -> None:
    """Test we can validate a user login."""
    with _reset_log_level():
        data = provider.data
        data.add_auth("test-user", "test-pass")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            await script_auth.validate_login(
                hass, provider, Mock(username="test-user", password="test-pass")
            )
        expect(buf.getvalue()).to_equal("Auth valid\n")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            await script_auth.validate_login(
                hass, provider, Mock(username="test-user", password="invalid-pass")
            )
        expect(buf.getvalue()).to_equal("Auth invalid\n")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            await script_auth.validate_login(
                hass, provider, Mock(username="invalid-user", password="test-pass")
            )
        expect(buf.getvalue()).to_equal("Auth invalid\n")


@test
async def change_password(
    hass: HomeAssistant = Depends(hass),
    provider: hass_auth.HassAuthProvider = Depends(provider),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test we can change a password."""
    with _reset_log_level():
        data = provider.data
        data.add_auth("test-user", "test-pass")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            await script_auth.change_password(
                hass, provider, Mock(username="test-user", new_password="new-pass")
            )

        expect(len(hass_storage[hass_auth.STORAGE_KEY]["data"]["users"])).to_equal(1)
        expect(buf.getvalue()).to_equal("Password changed\n")
        data.validate_login("test-user", "new-pass")
        expect(lambda: data.validate_login("test-user", "test-pass")).to_raise(
            hass_auth.InvalidAuth
        )


@test
async def change_password_invalid_user(
    hass: HomeAssistant = Depends(hass),
    provider: hass_auth.HassAuthProvider = Depends(provider),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test changing password of non-existing user."""
    with _reset_log_level():
        data = provider.data
        data.add_auth("test-user", "test-pass")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            await script_auth.change_password(
                hass, provider, Mock(username="invalid-user", new_password="new-pass")
            )

        expect(hass_auth.STORAGE_KEY not in hass_storage).to_be(True)
        expect(buf.getvalue()).to_equal("User not found\n")
        data.validate_login("test-user", "test-pass")
        expect(lambda: data.validate_login("invalid-user", "new-pass")).to_raise(
            hass_auth.InvalidAuth
        )


@test
async def parsing_args() -> None:
    """Test we parse args correctly."""
    called = False

    async def mock_func(
        hass: HomeAssistant,
        provider: hass_auth.AuthProvider,
        args2: argparse.Namespace,
    ) -> None:
        """Mock function to be called."""
        nonlocal called
        called = True
        expect(provider.hass.config.config_dir).to_equal("/somewhere/config")
        expect(args2 is args).to_be(True)

    args = Mock(config="/somewhere/config", func=mock_func)

    event_loop = asyncio.get_event_loop()
    with patch("argparse.ArgumentParser.parse_args", return_value=args):
        await event_loop.run_in_executor(None, script_auth.run, None)

    expect(called).to_be(True)
