"""Tryke fixtures for the UpCloud tests."""

from collections.abc import Generator

import requests_mock as rm
from tryke import fixture


@fixture
def requests_mock_mocker() -> Generator[rm.Mocker]:
    """Provide a requests_mock Mocker context manager."""
    with rm.Mocker() as mocker:
        yield mocker
