"""Tryke fixtures for the iZone integration."""

from unittest.mock import Mock

from tryke import fixture


@fixture
def mock_disco() -> Mock:
    """Mock discovery service."""
    disco = Mock()
    disco.pi_disco = Mock()
    disco.pi_disco.controllers = {}
    return disco
