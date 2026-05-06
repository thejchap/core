"""Tryke fixtures for the Tailwind integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from gotailwind import TailwindDeviceStatus
from tryke import fixture

from homeassistant.components.tailwind.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_TOKEN

from tests.common import MockConfigEntry, load_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Tailwind iQ3",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.127",
            CONF_TOKEN: "123456",
        },
        unique_id="3c:e9:0e:6d:21:84",
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.tailwind.async_setup_entry", return_value=True
    ):
        yield


@fixture
def mock_tailwind() -> Generator[MagicMock]:
    """Return a mocked Tailwind client."""
    with (
        patch(
            "homeassistant.components.tailwind.coordinator.Tailwind", autospec=True
        ) as tailwind_mock,
        patch(
            "homeassistant.components.tailwind.config_flow.Tailwind",
            new=tailwind_mock,
        ),
    ):
        tailwind = tailwind_mock.return_value
        tailwind.status.return_value = TailwindDeviceStatus.from_json(
            load_fixture("iq3.json", DOMAIN)
        )
        yield tailwind
