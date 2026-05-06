"""Define tests for the RainMachine config flow."""

from __future__ import annotations

from ipaddress import ip_address
from typing import Any
from unittest.mock import AsyncMock, patch

from regenmaschine.errors import RainMachineError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, setup
from homeassistant.components.rainmachine import (
    CONF_ALLOW_INACTIVE_ZONES_TO_RUN,
    CONF_DEFAULT_ZONE_RUN_TIME,
    CONF_USE_APP_RUN_TIMES,
    DOMAIN,
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_PORT, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    client as client_fx,
    config as config_fx,
    config_entry as config_entry_fx,
    setup_rainmachine as setup_rainmachine_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import entity_registry as entity_registry_fx, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


def _zeroconf_data(ip: str) -> ZeroconfServiceInfo:
    return ZeroconfServiceInfo(
        ip_address=ip_address(ip),
        ip_addresses=[ip_address(ip)],
        hostname="mock_hostname",
        name="mock_name",
        port=None,
        properties={},
        type="mock_type",
    )


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, Any] = Depends(config_fx),
    _entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test that errors are shown when duplicates are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=cfg
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def invalid_password(
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, Any] = Depends(config_fx),
) -> None:
    """Test that an invalid password throws an error."""
    with patch(
        "regenmaschine.client.Client.load_local", side_effect=RainMachineError
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=cfg
        )
    expect(result["errors"]).to_equal({CONF_PASSWORD: "invalid_auth"})


@test.cases(
    test.case(
        "binary_sensor",
        platform="binary_sensor",
        entity_name="Home Flow Sensor",
        entity_id="binary_sensor.home_flow_sensor",
        old_unique_id="60e32719b6cf_flow_sensor",
        new_unique_id="60:e3:27:19:b6:cf_flow_sensor",
    ),
    test.case(
        "switch",
        platform="switch",
        entity_name="Home Landscaping",
        entity_id="switch.home_landscaping",
        old_unique_id="60e32719b6cf_RainMachineZone_1",
        new_unique_id="60:e3:27:19:b6:cf_zone_1",
    ),
)
async def migrate_1_2(
    *,
    platform: str,
    entity_name: str,
    entity_id: str,
    old_unique_id: str,
    new_unique_id: str,
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    client_mock: AsyncMock = Depends(client_fx),
    entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test migration from version 1 to 2 (consistent unique IDs)."""
    entity_entry = entity_registry.async_get_or_create(
        platform,
        DOMAIN,
        old_unique_id,
        suggested_object_id=entity_name,
        config_entry=entry,
        original_name=entity_name,
    )
    expect(entity_entry.entity_id).to_equal(entity_id)
    expect(entity_entry.unique_id).to_equal(old_unique_id)

    with (
        patch(
            "homeassistant.components.rainmachine.async_setup_entry", return_value=True
        ),
        patch(
            "homeassistant.components.rainmachine.config_flow.Client",
            return_value=client_mock,
        ),
    ):
        await setup.async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

    updated = entity_registry.async_get(entity_id)
    expect(updated.unique_id).to_equal(new_unique_id)
    expect(
        entity_registry.async_get_entity_id(platform, DOMAIN, old_unique_id)
    ).to_be(None)


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, Any] = Depends(config_fx),
    entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test config flow options."""
    with patch(
        "homeassistant.components.rainmachine.async_setup_entry", return_value=True
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        result = await hass.config_entries.options.async_init(entry.entry_id)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_DEFAULT_ZONE_RUN_TIME: 600,
                CONF_USE_APP_RUN_TIMES: False,
                CONF_ALLOW_INACTIVE_ZONES_TO_RUN: False,
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(entry.options).to_equal(
            {
                CONF_DEFAULT_ZONE_RUN_TIME: 600,
                CONF_USE_APP_RUN_TIMES: False,
                CONF_ALLOW_INACTIVE_ZONES_TO_RUN: False,
            }
        )


@test
async def show_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=None
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def step_user(
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, Any] = Depends(config_fx),
    _setup: None = Depends(setup_rainmachine_fx),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=cfg
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("12345")
    expect(result["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_PASSWORD: "password",
            CONF_PORT: 8080,
            CONF_SSL: True,
            CONF_DEFAULT_ZONE_RUN_TIME: 600,
        }
    )


@test.cases(
    test.case("zeroconf", source=config_entries.SOURCE_ZEROCONF),
    test.case("homekit", source=config_entries.SOURCE_HOMEKIT),
)
async def step_homekit_zeroconf_ip_already_exists(
    *,
    source: str,
    hass: HomeAssistant = Depends(hass_fixture),
    client_mock: AsyncMock = Depends(client_fx),
    _entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test homekit and zeroconf with an ip that already exists."""
    with patch(
        "homeassistant.components.rainmachine.config_flow.Client",
        return_value=client_mock,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=_zeroconf_data("192.168.1.100"),
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("zeroconf", source=config_entries.SOURCE_ZEROCONF),
    test.case("homekit", source=config_entries.SOURCE_HOMEKIT),
)
async def step_homekit_zeroconf_ip_change(
    *,
    source: str,
    hass: HomeAssistant = Depends(hass_fixture),
    client_mock: AsyncMock = Depends(client_fx),
    entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test zeroconf with an ip change."""
    with patch(
        "homeassistant.components.rainmachine.config_flow.Client",
        return_value=client_mock,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=_zeroconf_data("192.168.1.2"),
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal("192.168.1.2")


@test.cases(
    test.case("zeroconf", source=config_entries.SOURCE_ZEROCONF),
    test.case("homekit", source=config_entries.SOURCE_HOMEKIT),
)
async def step_homekit_zeroconf_new_controller_when_some_exist(
    *,
    source: str,
    hass: HomeAssistant = Depends(hass_fixture),
    client_mock: AsyncMock = Depends(client_fx),
    _cfg: dict[str, Any] = Depends(config_fx),
) -> None:
    """Test homekit and zeroconf for a new controller when one already exists."""
    with patch(
        "homeassistant.components.rainmachine.config_flow.Client",
        return_value=client_mock,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=_zeroconf_data("192.168.1.100"),
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.rainmachine.async_setup_entry", return_value=True
        ),
        patch(
            "homeassistant.components.rainmachine.config_flow.Client",
            return_value=client_mock,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PASSWORD: "password",
                CONF_PORT: 8080,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("12345")
    expect(result2["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_PASSWORD: "password",
            CONF_PORT: 8080,
            CONF_SSL: True,
            CONF_DEFAULT_ZONE_RUN_TIME: 600,
        }
    )


@test
async def discovery_by_homekit_and_zeroconf_same_time(
    hass: HomeAssistant = Depends(hass_fixture),
    client_mock: AsyncMock = Depends(client_fx),
) -> None:
    """Test the same controller gets discovered by two different methods."""
    with patch(
        "homeassistant.components.rainmachine.config_flow.Client",
        return_value=client_mock,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=_zeroconf_data("192.168.1.100"),
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.rainmachine.config_flow.Client",
        return_value=client_mock,
    ):
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_HOMEKIT},
            data=_zeroconf_data("192.168.1.100"),
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_in_progress")
