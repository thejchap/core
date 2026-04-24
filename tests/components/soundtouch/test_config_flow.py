"""Test config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import patch

from requests import RequestException
from requests_mock import ANY, Mocker
from tryke import Depends, expect, fixture, test

from homeassistant.components.soundtouch.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    DEVICE_1_ID,
    DEVICE_1_IP,
    DEVICE_1_NAME,
    device1_requests_mock_standby,
    requests_mocker,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock: Mocker = Depends(device1_requests_mock_standby),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    with patch(
        "homeassistant.components.soundtouch.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: DEVICE_1_IP},
        )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(DEVICE_1_NAME)
    expect(result.get("data")).to_equal({CONF_HOST: DEVICE_1_IP})
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal(DEVICE_1_ID)
    expect(result["result"].title).to_equal(DEVICE_1_NAME)


@test
async def user_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock: Mocker = Depends(requests_mocker),
) -> None:
    """Test a manual user flow with an invalid host."""
    mock.get(ANY, exc=RequestException())

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data={CONF_HOST: "invalid-hostname"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def zeroconf_flow_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock: Mocker = Depends(device1_requests_mock_standby),
) -> None:
    """Test the zeroconf flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(DEVICE_1_IP),
            ip_addresses=[ip_address(DEVICE_1_IP)],
            port=8090,
            hostname="Bose-SM2-060000000001.local.",
            type="_soundtouch._tcp.local.",
            name=f"{DEVICE_1_NAME}._soundtouch._tcp.local.",
            properties={
                "DESCRIPTION": "SoundTouch",
                "MAC": DEVICE_1_ID,
                "MANUFACTURER": "Bose Corporation",
                "MODEL": "SoundTouch",
            },
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("zeroconf_confirm")
    expect(result.get("description_placeholders")).to_equal({"name": DEVICE_1_NAME})

    with patch(
        "homeassistant.components.soundtouch.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(DEVICE_1_NAME)
    expect(result.get("data")).to_equal({CONF_HOST: DEVICE_1_IP})
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal(DEVICE_1_ID)
    expect(result["result"].title).to_equal(DEVICE_1_NAME)
