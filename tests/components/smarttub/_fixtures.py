"""Tryke fixtures for smarttub config flow tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, create_autospec, patch

import smarttub
from tryke import Depends, fixture

from homeassistant.components.smarttub.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from tests.common import MockConfigEntry


@fixture
def config_data() -> dict[str, Any]:
    """Provide configuration data for tests."""
    return {CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"}


@fixture
def spa() -> MagicMock:
    """Mock a smarttub.Spa (minimal for config flow)."""
    mock_spa = create_autospec(smarttub.Spa, instance=True)
    mock_spa.id = "mockspa1"
    mock_spa.brand = "mockbrand1"
    mock_spa.model = "mockmodel1"
    return mock_spa


@fixture
def account(spa_mock: MagicMock = Depends(spa)) -> MagicMock:
    """Mock a SmartTub.Account."""
    mock_account = create_autospec(smarttub.Account, instance=True)
    mock_account.id = "mockaccount1"
    mock_account.get_spas.return_value = [spa_mock]
    return mock_account


@fixture
def smarttub_api(
    account_mock: MagicMock = Depends(account),
) -> Generator[MagicMock]:
    """Mock the SmartTub API."""
    with patch(
        "homeassistant.components.smarttub.controller.SmartTub",
        autospec=True,
    ) as api_class_mock:
        api_mock = api_class_mock.return_value
        api_mock.get_account.return_value = account_mock
        yield api_mock


@fixture
def mock_setup_entry() -> Generator[MagicMock]:
    """Mock the integration setup."""
    with patch(
        "homeassistant.components.smarttub.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@fixture
def config_entry(
    data: dict[str, Any] = Depends(config_data),
    account_mock: MagicMock = Depends(account),
) -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=data,
        options={},
        unique_id=account_mock.id,
    )
