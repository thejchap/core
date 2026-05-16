"""Tryke fixtures for Bond tests."""

from tryke import Depends, fixture

from tests.hass_fixtures import mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Anchor module-level fixtures."""
    return 0
