"""Tryke fixtures for Logger component tests."""

from collections.abc import Generator
import logging

from tryke import Depends, fixture

from tests.hass_fixtures import mock_network


@fixture
def restore_logging_class() -> Generator[None]:
    """Restore logging class (autouse equivalent)."""
    klass = logging.getLoggerClass()
    yield
    logging.setLoggerClass(klass)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _restore_logging_class: None = Depends(restore_logging_class),
) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0
