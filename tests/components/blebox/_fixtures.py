"""Tryke fixtures for the BleBox integration."""

from unittest.mock import AsyncMock, PropertyMock

import blebox_uniapi
from tryke import fixture

from .conftest import mock_only_feature, setup_product_mock


def _create_valid_feature_mock(path: str = "homeassistant.components.blebox.Products"):
    """Return a valid, complete BleBox feature mock."""
    feature = mock_only_feature(
        blebox_uniapi.cover.Cover,
        unique_id="BleBox-gateBox-1afe34db9437-0.position",
        full_name="gateBox-0.position",
        device_class="gate",
        state=0,
        async_update=AsyncMock(),
        current=None,
    )

    product = setup_product_mock("covers", [feature], path)

    type(product).name = PropertyMock(return_value="My gate controller")
    type(product).model = PropertyMock(return_value="gateController")
    type(product).type = PropertyMock(return_value="gateBox")
    type(product).brand = PropertyMock(return_value="BleBox")
    type(product).firmware_version = PropertyMock(return_value="1.23")
    type(product).unique_id = PropertyMock(return_value="abcd0123ef5678")

    return feature


@fixture
def valid_feature_mock() -> object:
    """Return a valid, complete BleBox feature mock."""
    return _create_valid_feature_mock()


@fixture
def flow_feature_mock() -> object:
    """Return a mocked user flow feature."""
    return _create_valid_feature_mock(
        "homeassistant.components.blebox.config_flow.Products"
    )
