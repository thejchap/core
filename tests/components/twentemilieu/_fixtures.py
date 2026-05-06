"""Tryke fixtures for the Twente Milieu integration tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from unittest.mock import MagicMock, patch

from twentemilieu import WasteType
from tryke import fixture

from homeassistant.components.twentemilieu.const import (
    CONF_HOUSE_LETTER,
    CONF_HOUSE_NUMBER,
    CONF_POST_CODE,
    DOMAIN,
)
from homeassistant.const import CONF_ID

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="1234AB 1",
        domain=DOMAIN,
        data={
            CONF_ID: 12345,
            CONF_POST_CODE: "1234AB",
            CONF_HOUSE_NUMBER: "1",
            CONF_HOUSE_LETTER: "A",
        },
        unique_id="12345",
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.twentemilieu.async_setup_entry", return_value=True
    ):
        yield


@fixture
def mock_twentemilieu() -> Generator[MagicMock]:
    """Return a mocked Twente Milieu client."""
    with (
        patch(
            "homeassistant.components.twentemilieu.coordinator.TwenteMilieu",
            autospec=True,
        ) as twentemilieu_mock,
        patch(
            "homeassistant.components.twentemilieu.config_flow.TwenteMilieu",
            new=twentemilieu_mock,
        ),
    ):
        twentemilieu = twentemilieu_mock.return_value
        twentemilieu.unique_id.return_value = 12345
        twentemilieu.update.return_value = {
            WasteType.NON_RECYCLABLE: [date(2021, 11, 1), date(2021, 12, 1)],
            WasteType.ORGANIC: [date(2021, 11, 2)],
            WasteType.PACKAGES: [date(2021, 11, 3)],
            WasteType.PAPER: [],
            WasteType.TREE: [date(2022, 1, 6)],
        }
        yield twentemilieu
