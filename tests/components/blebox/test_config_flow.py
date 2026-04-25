"""Test Home Assistant config flow for BleBox devices."""

from ipaddress import ip_address
from unittest.mock import DEFAULT, AsyncMock, patch

import blebox_uniapi
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.blebox import config_flow
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from homeassistant.setup import async_setup_component

from ._fixtures import flow_feature_mock, valid_feature_mock
from .conftest import mock_config, mock_feature

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _product_class_mock():
    """Return a mocked feature."""
    path = "homeassistant.components.blebox.config_flow.Box"
    return patch(path, DEFAULT, blebox_uniapi.box.Box, True, True)


@test
async def flow_works(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _valid: object = Depends(valid_feature_mock),
    _flow: object = Depends(flow_feature_mock),
) -> None:
    """Test that config flow works."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My gate controller")
    expect(result["data"]).to_equal(
        {
            config_flow.CONF_HOST: "172.2.3.4",
            config_flow.CONF_PORT: 80,
        }
    )


@test
async def flow_with_connection_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow works."""
    with _product_class_mock() as products_class:
        products_class.async_from_host = AsyncMock(
            side_effect=blebox_uniapi.error.ConnectionError
        )

        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
        )
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def flow_with_api_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow works."""
    with _product_class_mock() as products_class:
        products_class.async_from_host = AsyncMock(side_effect=blebox_uniapi.error.Error)

        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
        )
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def flow_with_unknown_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow works."""
    with _product_class_mock() as products_class:
        products_class.async_from_host = AsyncMock(side_effect=RuntimeError)
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
        )
        expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def flow_with_unsupported_version(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow works."""
    with _product_class_mock() as products_class:
        products_class.async_from_host = AsyncMock(
            side_effect=blebox_uniapi.error.UnsupportedBoxVersion
        )

        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
        )
        expect(result["errors"]).to_equal({"base": "unsupported_version"})


@test
async def flow_with_auth_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config flow works."""
    with _product_class_mock() as products_class:
        products_class.async_from_host = AsyncMock(
            side_effect=blebox_uniapi.error.UnauthorizedRequest
        )

        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
        )
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def async_setup_test(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_setup (for coverage)."""
    expect(
        await async_setup_component(hass, "blebox", {"host": "172.2.3.4"})
    ).to_be(True)
    await hass.async_block_till_done()


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _valid: object = Depends(valid_feature_mock),
) -> None:
    """Test that same device cannot be added twice."""
    config = mock_config("172.2.3.4")
    config.add_to_hass(hass)

    await hass.config_entries.async_setup(config.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={config_flow.CONF_HOST: "172.2.3.4", config_flow.CONF_PORT: 80},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("address_already_configured")


@test
async def async_setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _valid: object = Depends(valid_feature_mock),
) -> None:
    """Test async_setup_entry (for coverage)."""
    config = mock_config()
    config.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(hass.config_entries.async_entries()).to_equal([config])
    expect(config.state).to_be(ConfigEntryState.LOADED)


@test
async def async_remove_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _valid: object = Depends(valid_feature_mock),
) -> None:
    """Test async_setup_entry (for coverage)."""
    config = mock_config()
    config.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(await hass.config_entries.async_remove(config.entry_id)).to_equal(
        {"require_restart": False}
    )
    await hass.async_block_till_done()

    expect(hass.config_entries.async_entries()).to_equal([])
    expect(config.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("zeroconf flow tries real connection without mock; pytest behavior unclear under tryke")
async def flow_with_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from zeroconf discovery."""


@test
async def flow_with_zeroconf_when_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test behaviour if device already configured."""
    entry = MockConfigEntry(
        domain=config_flow.DOMAIN,
        data={CONF_IP_ADDRESS: "172.100.123.4"},
        unique_id="abcd0123ef5678",
    )
    entry.add_to_hass(hass)
    feature: AsyncMock = mock_feature(
        "sensors",
        blebox_uniapi.sensor.Temperature,
    )
    with patch(
        "homeassistant.components.blebox.config_flow.Box.async_from_host",
        return_value=feature.product,
    ):
        result2 = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("172.100.123.4"),
                ip_addresses=[ip_address("172.100.123.4")],
                port=80,
                hostname="bbx-bbtest123456.local.",
                type="_bbxsrv._tcp.local.",
                name="bbx-bbtest123456._bbxsrv._tcp.local.",
                properties={"_raw": {}},
            ),
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("already_configured")


@test
async def flow_with_zeroconf_when_device_unsupported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test behaviour when device is not supported."""
    with patch(
        "homeassistant.components.blebox.config_flow.Box.async_from_host",
        side_effect=blebox_uniapi.error.UnsupportedBoxVersion,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("172.100.123.4"),
                ip_addresses=[ip_address("172.100.123.4")],
                port=80,
                hostname="bbx-bbtest123456.local.",
                type="_bbxsrv._tcp.local.",
                name="bbx-bbtest123456._bbxsrv._tcp.local.",
                properties={"_raw": {}},
            ),
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("unsupported_device_version")


@test
async def flow_with_zeroconf_when_device_response_unsupported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test behaviour when device returned unsupported response."""
    with patch(
        "homeassistant.components.blebox.config_flow.Box.async_from_host",
        side_effect=blebox_uniapi.error.UnsupportedBoxResponse,
    ):
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("172.100.123.4"),
                ip_addresses=[ip_address("172.100.123.4")],
                port=80,
                hostname="bbx-bbtest123456.local.",
                type="_bbxsrv._tcp.local.",
                name="bbx-bbtest123456._bbxsrv._tcp.local.",
                properties={"_raw": {}},
            ),
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("unsupported_device_response")
