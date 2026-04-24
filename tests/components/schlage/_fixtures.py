"""Tryke fixtures for Schlage integration tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, create_autospec, patch

from pyschlage.lock import Lock
from tryke import Depends, fixture

from homeassistant.components.schlage.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import MockSchlageConfigEntry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_config_entry() -> MockSchlageConfigEntry:
    """Mock ConfigEntry."""
    return MockConfigEntry(
        title="asdf@asdf.com",
        domain=DOMAIN,
        data={
            CONF_USERNAME: "asdf@asdf.com",
            CONF_PASSWORD: "hunter2",
        },
        unique_id="abc123",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.schlage.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_schlage() -> Mock:
    """Mock pyschlage.Schlage."""
    with patch("pyschlage.Schlage", autospec=True) as mock_schlage:
        yield mock_schlage.return_value


@fixture
def mock_pyschlage_auth() -> Mock:
    """Mock pyschlage.Auth."""
    with patch("pyschlage.Auth", autospec=True) as mock_auth:
        mock_auth.return_value.user_id = "abc123"
        yield mock_auth.return_value


@fixture
def mock_lock_attrs() -> dict[str, Any]:
    """Attributes for a mock lock."""
    return {
        "device_id": "test",
        "name": "Vault Door",
        "model_name": "<model-name>",
        "is_locked": False,
        "is_jammed": False,
        "battery_level": 20,
        "auto_lock_time": 15,
        "firmware_version": "1.0",
        "lock_and_leave_enabled": True,
        "beeper_enabled": True,
    }


@fixture
def mock_lock(
    lock_attrs: dict[str, Any] = Depends(mock_lock_attrs),
) -> Mock:
    """Mock Lock fixture."""
    mock_lock = create_autospec(Lock)
    mock_lock.configure_mock(**lock_attrs)
    mock_lock.logs.return_value = []
    mock_lock.last_changed_by.return_value = "thumbturn"
    mock_lock.keypad_disabled.return_value = False
    return mock_lock


@fixture
async def mock_added_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockSchlageConfigEntry = Depends(mock_config_entry),
    pyschlage_auth: Mock = Depends(mock_pyschlage_auth),
    schlage: Mock = Depends(mock_schlage),
    lock: Mock = Depends(mock_lock),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> MockSchlageConfigEntry:
    """Mock ConfigEntry that's been added to HA."""
    schlage.locks.return_value = [lock]
    schlage.users.return_value = []
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN in hass.config_entries.async_domains()
    return config_entry
