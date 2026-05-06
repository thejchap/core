"""Test the Rachio config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.rachio.const import (
    CONF_CUSTOM_URL,
    CONF_MANUAL_RUN_MINS,
    DOMAIN,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import (
    ATTR_PROPERTIES_ID,
    ZeroconfServiceInfo,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


def _mock_rachio_return_value(get=None, info=None):
    rachio_mock = MagicMock()
    person_mock = MagicMock()
    type(person_mock).get = MagicMock(return_value=get)
    type(person_mock).info = MagicMock(return_value=info)
    type(rachio_mock).person = person_mock
    return rachio_mock


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    rachio_mock = _mock_rachio_return_value(
        get=({"status": 200}, {"username": "myusername"}),
        info=({"status": 200}, {"id": "myid"}),
    )

    with (
        patch(
            "homeassistant.components.rachio.config_flow.Rachio",
            return_value=rachio_mock,
        ),
        patch(
            "homeassistant.components.rachio.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "api_key",
                CONF_CUSTOM_URL: "http://custom.url",
                CONF_MANUAL_RUN_MINS: 5,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("myusername")
    expect(result2["data"]).to_equal(
        {
            CONF_API_KEY: "api_key",
            CONF_CUSTOM_URL: "http://custom.url",
            CONF_MANUAL_RUN_MINS: 5,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    rachio_mock = _mock_rachio_return_value(
        get=({"status": 200}, {"username": "myusername"}),
        info=({"status": 412}, {"error": "auth fail"}),
    )
    with patch(
        "homeassistant.components.rachio.config_flow.Rachio", return_value=rachio_mock
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "api_key"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    rachio_mock = _mock_rachio_return_value(
        get=({"status": 599}, {"username": "myusername"}),
        info=({"status": 200}, {"id": "myid"}),
    )
    with patch(
        "homeassistant.components.rachio.config_flow.Rachio", return_value=rachio_mock
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "api_key"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_homekit(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that we abort from homekit if rachio is already setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HOMEKIT},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=None,
            properties={ATTR_PROPERTIES_ID: "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    flow = next(
        f
        for f in hass.config_entries.flow.async_progress()
        if f["flow_id"] == result["flow_id"]
    )
    expect(flow["context"]["unique_id"]).to_equal("AA:BB:CC:DD:EE:FF")

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_API_KEY: "api_key"})
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HOMEKIT},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=None,
            properties={ATTR_PROPERTIES_ID: "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form_homekit_ignored(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that we abort from homekit if rachio is ignored."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HOMEKIT},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=None,
            properties={ATTR_PROPERTIES_ID: "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def options_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test option flow."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_API_KEY: "api_key"})
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    hass.config_entries.options.async_abort(result["flow_id"])
