"""Test the ROMY config flow."""

from __future__ import annotations

from collections.abc import Generator
from ipaddress import ip_address
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

from romy import RomyRobot
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.romy.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import (
    ATTR_PROPERTIES_ID,
    ZeroconfServiceInfo,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


def _create_mocked_romy(
    is_initialized: bool,
    is_unlocked: bool,
    name: str = "Agon",
    user_name: str = "MyROMY",
    unique_id: str = "aicu-aicgsbksisfapcjqmqjq",
    model: str = "005:000:000:000:005",
    port: int = 8080,
) -> Mock:
    mocked_romy = Mock(spec_set=RomyRobot)
    type(mocked_romy).is_initialized = PropertyMock(return_value=is_initialized)
    type(mocked_romy).is_unlocked = PropertyMock(return_value=is_unlocked)
    type(mocked_romy).name = PropertyMock(return_value=name)
    type(mocked_romy).user_name = PropertyMock(return_value=user_name)
    type(mocked_romy).unique_id = PropertyMock(return_value=unique_id)
    type(mocked_romy).port = PropertyMock(return_value=port)
    type(mocked_romy).model = PropertyMock(return_value=model)
    return mocked_romy


CONFIG = {CONF_HOST: "1.2.3.4", CONF_PASSWORD: "12345678"}
INPUT_CONFIG_HOST = {CONF_HOST: CONFIG[CONF_HOST]}
DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address("1.2.3.4"),
    ip_addresses=[ip_address("1.2.3.4")],
    port=8080,
    hostname="aicu-aicgsbksisfapcjqmqjq.local",
    type="mock_type",
    name="myROMY",
    properties={ATTR_PROPERTIES_ID: "aicu-aicgsbksisfapcjqmqjqZERO"},
)


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.romy.async_setup_entry", return_value=True
    ) as m:
        yield m


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Wire mock_network and mock_setup_entry for every test."""


@test
async def show_user_form_robot_is_offline_and_locked(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user set up form with config."""
    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(False, False),
    ):
        result1 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG_HOST,
        )
        expect(result1["errors"].get("host")).to_equal("cannot_connect")
        expect(result1["step_id"]).to_equal("user")
        expect(result1["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, False),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"], {"host": "1.2.3.4"}
        )
        expect(result2["step_id"]).to_equal("password")
        expect(result2["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, True),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {"password": "12345678"}
        )
        expect("errors" not in result3).to_be(True)
        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def show_user_form_robot_unlock_with_password(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user set up form with config."""
    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, False),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG_HOST,
        )

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, False),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"password": "12345678"}
        )
        expect(result2["errors"]).to_equal({"password": "invalid_auth"})
        expect(result2["step_id"]).to_equal("password")
        expect(result2["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(False, False),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {"password": "12345678"}
        )
        expect(result3["errors"]).to_equal({"password": "cannot_connect"})
        expect(result3["step_id"]).to_equal("password")
        expect(result3["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, True),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"], {"password": "12345678"}
        )
        expect("errors" not in result4).to_be(True)
        expect(result4["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def show_user_form_robot_reachable_again(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user set up form with config."""
    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(False, False),
    ):
        result1 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG_HOST,
        )
        expect(result1["errors"].get("host")).to_equal("cannot_connect")
        expect(result1["step_id"]).to_equal("user")
        expect(result1["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, True),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"], {"host": "1.2.3.4"}
        )
        expect("errors" not in result2).to_be(True)
        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zero_conf_locked_interface_robot(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zerconf which discovered locked robot."""
    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, False),
    ):
        result1 = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    expect(result1["step_id"]).to_equal("password")
    expect(result1["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, True),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"], {"password": "12345678"}
        )
        expect("errors" not in result2).to_be(True)
        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zero_conf_uninitialized_robot(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zerconf which discovered locked robot."""
    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(False, False),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    expect(result["reason"]).to_equal("cannot_connect")
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def zero_conf_unlocked_interface_robot(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zerconf which discovered already unlocked robot."""
    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "1.2.3.4"},
    )

    expect(bool(result["data"])).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal("1.2.3.4")
    expect(bool(result["result"])).to_be(True)
    expect(result["result"].unique_id).to_equal("aicu-aicgsbksisfapcjqmqjq")
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
