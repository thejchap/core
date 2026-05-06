"""Tryke fixtures for Wemo tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, create_autospec, patch

import pywemo
from tryke import Depends, fixture


@fixture
def pywemo_registry() -> Generator[MagicMock]:
    """Fixture for SubscriptionRegistry instances."""
    registry = create_autospec(pywemo.SubscriptionRegistry, instance=True)

    registry.callbacks = {}

    def on_func(device, type_filter, callback):
        registry.callbacks[device.name] = callback

    registry.on.side_effect = on_func
    registry.is_subscribed.return_value = False

    with patch("pywemo.SubscriptionRegistry", return_value=registry):
        yield registry


@fixture
def pywemo_discovery_responder(
    _registry: MagicMock = Depends(pywemo_registry),
) -> Generator[None]:
    """Fixture for the DiscoveryResponder instance."""
    with patch("pywemo.ssdp.DiscoveryResponder", autospec=True):
        yield
