"""Tryke fixtures for the Moat BLE integration tests."""

from tryke import Depends, fixture

from tests.hass_fixtures import enable_bluetooth as enable_bluetooth_fixture


@fixture
def mock_bluetooth(
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> None:
    """Auto mock bluetooth."""
