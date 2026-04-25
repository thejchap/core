"""Tryke fixtures for the Met Office integration."""

from collections.abc import Generator
from unittest.mock import patch

from datapoint.exceptions import APIException
import requests_mock as requests_mock_lib
from tryke import fixture


@fixture
def requests_mock() -> Generator[requests_mock_lib.Mocker]:
    """Provide a requests_mock context."""
    with requests_mock_lib.Mocker() as m:
        yield m


@fixture
def mock_simple_manager_fail():
    """Mock datapoint Manager with default values for testing in config_flow."""
    with patch(
        "homeassistant.components.metoffice.config_flow.Manager"
    ) as mock_manager:
        instance = mock_manager.return_value
        instance.get_forecast = APIException()
        instance.latitude = None
        instance.longitude = None
        instance.site = None
        instance.site_id = None
        instance.site_name = None
        instance.now = None

        yield mock_manager
