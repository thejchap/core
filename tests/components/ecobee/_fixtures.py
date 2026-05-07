"""Tryke fixtures for the Ecobee integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import requests_mock as rm_lib
from tryke import Depends, fixture

from tests.common import load_fixture
from tests.hass_tryke_helpers import requests_mock_session


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ecobee.async_setup_entry", return_value=True
    ) as mock:
        yield mock


@fixture
def requests_mock_fixture(
    requests_mock: rm_lib.Mocker = Depends(requests_mock_session),
) -> rm_lib.Mocker:
    """Provide a requests mocker pre-loaded with Ecobee API endpoints."""
    requests_mock.get(
        "https://api.ecobee.com/1/thermostat",
        text=load_fixture("ecobee/ecobee-data.json"),
    )
    requests_mock.post(
        "https://api.ecobee.com/token",
        text=load_fixture("ecobee/ecobee-token.json"),
    )
    return requests_mock
