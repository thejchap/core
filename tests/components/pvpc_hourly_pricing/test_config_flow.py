"""Tests for the pvpc_hourly_pricing config_flow."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.pvpc_hourly_pricing.const import (
    ATTR_POWER,
    ATTR_POWER_P3,
    ATTR_TARIFF,
    CONF_USE_API_TOKEN,
    DOMAIN,
    TARIFFS,
)
from homeassistant.const import CONF_API_TOKEN, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from ._fixtures import (
    check_valid_state,
    pvpc_aioclient_mock as pvpc_aioclient_mock_fx,
)

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    freezer as freezer_fx,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

_MOCK_TIME_VALID_RESPONSES = datetime(2023, 1, 6, 12, 0, tzinfo=dt_util.UTC)
_MOCK_TIME_BAD_AUTH_RESPONSES = datetime(2023, 1, 8, 12, 0, tzinfo=dt_util.UTC)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def config_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    pvpc_aioclient_mock: AiohttpClientMocker = Depends(pvpc_aioclient_mock_fx),
) -> None:
    """Test config flow for pvpc_hourly_pricing."""
    freezer.move_to(_MOCK_TIME_VALID_RESPONSES)
    await hass.config.async_set_time_zone("Europe/Madrid")
    tst_config: dict[str, Any] = {
        CONF_NAME: "test",
        ATTR_TARIFF: TARIFFS[1],
        ATTR_POWER: 4.6,
        ATTR_POWER_P3: 5.75,
        CONF_USE_API_TOKEN: False,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], tst_config
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    await hass.async_block_till_done()
    state = hass.states.get("sensor.esios_pvpc")
    check_valid_state(state, tariff=TARIFFS[1])
    expect(pvpc_aioclient_mock.call_count).to_equal(1)

    state_inyection = hass.states.get("sensor.injection_price")
    expect(state_inyection is None).to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], tst_config
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(pvpc_aioclient_mock.call_count).to_equal(1)

    registry_entity = entity_registry.async_get("sensor.esios_pvpc")
    assert registry_entity is not None
    expect(
        bool(await hass.config_entries.async_remove(registry_entity.config_entry_id))
    ).to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], tst_config
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    await hass.async_block_till_done()
    state = hass.states.get("sensor.esios_pvpc")
    check_valid_state(state, tariff=TARIFFS[1])
    expect(pvpc_aioclient_mock.call_count).to_equal(2)
    expect(state.attributes["period"]).to_equal("P3")
    expect(state.attributes["next_period"]).to_equal("P2")
    expect(state.attributes["available_power"]).to_equal(5750)

    current_entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(current_entries)).to_equal(1)
    config_entry = current_entries[0]

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={ATTR_POWER: 3.0, ATTR_POWER_P3: 4.6, CONF_USE_API_TOKEN: True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_token")
    expect(pvpc_aioclient_mock.call_count).to_equal(2)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.esios_pvpc")
    check_valid_state(state, tariff=TARIFFS[1])
    expect(pvpc_aioclient_mock.call_count).to_equal(3)
    expect(state.attributes["period"]).to_equal("P3")
    expect(state.attributes["next_period"]).to_equal("P2")
    expect(state.attributes["available_power"]).to_equal(4600)

    state_inyection = hass.states.get("sensor.esios_injection_price")
    state_mag = hass.states.get("sensor.esios_mag_tax")
    state_omie = hass.states.get("sensor.esios_omie_price")
    expect(state_inyection is not None).to_be(True)
    expect(state_mag is None).to_be(True)
    expect(state_omie is None).to_be(True)
    assert state_inyection is not None
    expect("period" in state_inyection.attributes).to_be(False)
    expect("available_power" in state_inyection.attributes).to_be(False)

    freezer.tick(timedelta(days=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.esios_pvpc")
    check_valid_state(state, tariff=TARIFFS[0], value="unavailable")
    expect("period" in state.attributes).to_be(False)
    expect(pvpc_aioclient_mock.call_count).to_equal(5)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={ATTR_POWER: 3.0, ATTR_POWER_P3: 4.6, CONF_USE_API_TOKEN: False},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    await hass.async_block_till_done()
    expect(pvpc_aioclient_mock.call_count).to_equal(6)

    state = hass.states.get("sensor.esios_pvpc")
    state_inyection = hass.states.get("sensor.esios_injection_price")
    state_mag = hass.states.get("sensor.esios_mag_tax")
    state_omie = hass.states.get("sensor.esios_omie_price")
    check_valid_state(state, tariff=TARIFFS[1])
    expect(state_inyection.state).to_equal("unavailable")
    expect(state_mag is None).to_be(True)
    expect(state_omie is None).to_be(True)


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    pvpc_aioclient_mock: AiohttpClientMocker = Depends(pvpc_aioclient_mock_fx),
) -> None:
    """Test reauth flow for API-token mode."""
    freezer.move_to(_MOCK_TIME_BAD_AUTH_RESPONSES)
    await hass.config.async_set_time_zone("Europe/Madrid")
    tst_config: dict[str, Any] = {
        CONF_NAME: "test",
        ATTR_TARIFF: TARIFFS[1],
        ATTR_POWER: 4.6,
        ATTR_POWER_P3: 5.75,
        CONF_USE_API_TOKEN: True,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], tst_config
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_token")
    expect(pvpc_aioclient_mock.call_count).to_equal(0)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_token")
    expect(result["errors"]["base"]).to_equal("invalid_auth")
    expect(pvpc_aioclient_mock.call_count).to_equal(1)

    freezer.move_to(_MOCK_TIME_VALID_RESPONSES)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    config_entry = result["result"]
    expect(pvpc_aioclient_mock.call_count).to_equal(4)

    freezer.move_to(_MOCK_TIME_BAD_AUTH_RESPONSES)
    async_fire_time_changed(hass, _MOCK_TIME_BAD_AUTH_RESPONSES)
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(pvpc_aioclient_mock.call_count).to_equal(6)

    result = hass.config_entries.flow.async_progress_by_handler(DOMAIN)[0]
    expect(result["context"]["entry_id"]).to_equal(config_entry.entry_id)
    expect(result["context"]["source"]).to_equal(config_entries.SOURCE_REAUTH)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(pvpc_aioclient_mock.call_count).to_equal(7)

    result = hass.config_entries.flow.async_progress_by_handler(DOMAIN)[0]
    expect(result["context"]["entry_id"]).to_equal(config_entry.entry_id)
    expect(result["context"]["source"]).to_equal(config_entries.SOURCE_REAUTH)
    expect(result["step_id"]).to_equal("reauth_confirm")

    freezer.move_to(_MOCK_TIME_VALID_RESPONSES)
    async_fire_time_changed(hass, _MOCK_TIME_VALID_RESPONSES)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(pvpc_aioclient_mock.call_count).to_equal(8)

    await hass.async_block_till_done(wait_background_tasks=True)
    expect(pvpc_aioclient_mock.call_count).to_equal(10)
