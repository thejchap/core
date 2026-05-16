"""Tryke fixtures for the BleBox integration."""

from unittest.mock import AsyncMock, PropertyMock

import blebox_uniapi
from tryke import fixture

from .conftest import mock_feature, mock_only_feature, setup_product_mock


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


def _make_shutterbox() -> tuple[object, str]:
    """Return a shutterBox fixture (feature_mock, entity_id)."""
    feature = mock_feature(
        "covers",
        blebox_uniapi.cover.Cover,
        unique_id="BleBox-shutterBox-2bee34e750b8-position",
        full_name="shutterBox-position",
        device_class="shutter",
        current=None,
        tilt_current=None,
        state=None,
        has_stop=True,
        has_tilt=True,
        is_slider=True,
        is_position_inverted=True,
    )
    product = feature.product
    type(product).name = PropertyMock(return_value="My shutter")
    type(product).model = PropertyMock(return_value="shutterBox")
    return (feature, "cover.my_shutter_shutterbox_position")


def _make_gatebox() -> tuple[object, str]:
    """Return a gateBox fixture (feature_mock, entity_id)."""
    feature = mock_feature(
        "covers",
        blebox_uniapi.cover.Cover,
        unique_id="BleBox-gateBox-1afe34db9437-position",
        device_class="gatebox",
        full_name="gateBox-position",
        current=None,
        state=None,
        has_stop=False,
        is_slider=False,
        is_position_inverted=False,
    )
    product = feature.product
    type(product).name = PropertyMock(return_value="My gatebox")
    type(product).model = PropertyMock(return_value="gateBox")
    return (feature, "cover.my_gatebox_gatebox_position")


def _make_gatecontroller() -> tuple[object, str]:
    """Return a gateController fixture (feature_mock, entity_id)."""
    feature = mock_feature(
        "covers",
        blebox_uniapi.cover.Cover,
        unique_id="BleBox-gateController-2bee34e750b8-position",
        full_name="gateController-position",
        device_class="gate",
        current=None,
        state=None,
        has_stop=True,
        is_slider=True,
        is_position_inverted=True,
    )
    product = feature.product
    type(product).name = PropertyMock(return_value="My gate controller")
    type(product).model = PropertyMock(return_value="gateController")
    return (feature, "cover.my_gate_controller_gatecontroller_position")


@fixture
def shutterbox() -> tuple[object, str]:
    """Return a shutterBox fixture."""
    return _make_shutterbox()


@fixture
def gatebox() -> tuple[object, str]:
    """Return a gateBox fixture."""
    return _make_gatebox()


@fixture
def gatecontroller() -> tuple[object, str]:
    """Return a gateController fixture."""
    return _make_gatecontroller()


def _make_dimmer() -> tuple[object, str]:
    """Return a dimmer fixture (feature_mock, entity_id)."""
    feature = mock_feature(
        "lights",
        blebox_uniapi.light.Light,
        unique_id="BleBox-dimmerBox-1afe34e750b8-brightness",
        full_name="dimmerBox-brightness",
        device_class=None,
        brightness=65,
        is_on=True,
        supports_color=False,
        supports_white=False,
        color_mode=blebox_uniapi.light.BleboxColorMode.MONO,
        effect_list=None,
    )
    product = feature.product
    type(product).name = PropertyMock(return_value="My dimmer")
    type(product).model = PropertyMock(return_value="dimmerBox")
    return (feature, "light.my_dimmer_dimmerbox_brightness")


def _make_wlightbox_s() -> tuple[object, str]:
    """Return a wLightBoxS fixture (feature_mock, entity_id)."""
    feature = mock_feature(
        "lights",
        blebox_uniapi.light.Light,
        unique_id="BleBox-wLightBoxS-1afe34e750b8-color",
        full_name="wLightBoxS-color",
        device_class=None,
        brightness=None,
        is_on=None,
        supports_color=False,
        supports_white=False,
        color_mode=blebox_uniapi.light.BleboxColorMode.MONO,
        effect_list=["NONE", "PL", "RELAX"],
    )
    product = feature.product
    type(product).name = PropertyMock(return_value="My wLightBoxS")
    type(product).model = PropertyMock(return_value="wLightBoxS")
    return (feature, "light.my_wlightboxs_wlightboxs_color")


def _make_wlightbox() -> tuple[object, str]:
    """Return a wLightBox fixture (feature_mock, entity_id)."""
    feature = mock_feature(
        "lights",
        blebox_uniapi.light.Light,
        unique_id="BleBox-wLightBox-1afe34e750b8-color",
        full_name="wLightBox-color",
        device_class=None,
        is_on=None,
        supports_color=True,
        supports_white=True,
        white_value=None,
        rgbw_hex=None,
        color_mode=blebox_uniapi.light.BleboxColorMode.RGBW,
        effect="NONE",
        effect_list=["NONE", "PL", "POLICE"],
    )
    product = feature.product
    type(product).name = PropertyMock(return_value="My wLightBox")
    type(product).model = PropertyMock(return_value="wLightBox")
    return (feature, "light.my_wlightbox_wlightbox_color")


@fixture
def dimmer() -> tuple[object, str]:
    """Return a dimmer fixture."""
    return _make_dimmer()


@fixture
def wlightbox_s() -> tuple[object, str]:
    """Return a wLightBoxS fixture."""
    return _make_wlightbox_s()


@fixture
def wlightbox() -> tuple[object, str]:
    """Return a wLightBox fixture."""
    return _make_wlightbox()
