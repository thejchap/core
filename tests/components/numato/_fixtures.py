"""Tryke fixtures for numato tests."""

from collections.abc import Generator
from copy import deepcopy
from typing import Any

from tryke import fixture

from homeassistant.components import numato

from .common import NUMATO_CFG
from .numato_mock import NumatoModuleMock


@fixture
def config() -> dict[str, Any]:
    """Provide a copy of the numato domain's test configuration.

    This helps to quickly change certain aspects of the configuration scoped
    to each individual test.
    """
    return deepcopy(NUMATO_CFG)


@fixture
def numato_fixture() -> Generator[NumatoModuleMock]:
    """Inject the numato mockup into numato homeassistant module."""
    module_mock = NumatoModuleMock()
    original = numato.gpio
    numato.gpio = module_mock
    try:
        yield module_mock
    finally:
        numato.gpio = original
