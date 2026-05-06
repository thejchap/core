"""Tryke fixtures for the Keenetic NDMS2 integration."""

from collections.abc import Generator
from unittest.mock import patch

from ndms2_client import ConnectionException
from ndms2_client.client import RouterInfo
from tryke import fixture

from . import MOCK_NAME


@fixture
def connect() -> Generator[None]:
    """Mock connection routine."""
    with patch("ndms2_client.client.Client.get_router_info") as mock_get_router_info:
        mock_get_router_info.return_value = RouterInfo(
            name=MOCK_NAME,
            fw_version="3.0.4",
            fw_channel="stable",
            model="mock",
            hw_version="0000",
            manufacturer="pytest",
            vendor="foxel",
            region="RU",
        )
        yield


@fixture
def connect_error() -> Generator[None]:
    """Mock connection routine that fails."""
    with patch(
        "ndms2_client.client.Client.get_router_info",
        side_effect=ConnectionException("Mocked failure"),
    ):
        yield
