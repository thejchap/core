"""Test deCONZ component setup process (tryke port)."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pydeconz
from tryke import Depends, expect, fixture, test

from homeassistant.components.deconz.const import CONF_MASTER_GATEWAY, DOMAIN
from homeassistant.components.deconz.errors import AuthenticationRequired
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.deconz._fixtures import (
    build_config_entry,
    register_get_request,
    setup_deconz,
)
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@test
async def setup_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test successful setup of entry."""
    config_entry_setup = await setup_deconz(hass, aioclient)
    expect(config_entry_setup.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry_setup.options[CONF_MASTER_GATEWAY]).to_be(True)


@test.cases(
    test.case(
        "unauthorized",
        side_effect=pydeconz.Unauthorized,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "timeout",
        side_effect=TimeoutError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "request_error",
        side_effect=pydeconz.RequestError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "response_error",
        side_effect=pydeconz.ResponseError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def get_deconz_api_fails(
    side_effect: type[Exception],
    state: ConfigEntryState,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Failed setup."""
    config_entry = build_config_entry()
    config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.deconz.hub.api.DeconzSession.refresh_state",
        side_effect=side_effect,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    expect(config_entry.state).to_be(state)


@test
async def setup_entry_fails_trigger_reauth_flow(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Failed authentication trigger a reauthentication flow."""
    with (
        patch(
            "homeassistant.components.deconz.get_deconz_api",
            side_effect=AuthenticationRequired,
        ),
        patch.object(hass.config_entries.flow, "async_init") as mock_flow_init,
    ):
        config_entry = await setup_deconz(hass, aioclient)
        mock_flow_init.assert_called_once()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def setup_entry_multiple_gateways(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test setup entry is successful with multiple gateways."""
    config_entry = await setup_deconz(hass, aioclient)

    entry2 = MockConfigEntry(
        domain=DOMAIN,
        entry_id="2",
        unique_id="01234E56789B",
        data=config_entry.data | {"host": "2.3.4.5"},
    )
    entry2.add_to_hass(hass)

    register_get_request(aioclient, host="2.3.4.5")
    await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry2.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.options[CONF_MASTER_GATEWAY]).to_be(True)
    expect(entry2.options[CONF_MASTER_GATEWAY]).to_be(False)


@test
async def unload_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test being able to unload an entry."""
    config_entry_setup = await setup_deconz(hass, aioclient)
    expect(config_entry_setup.state).to_be(ConfigEntryState.LOADED)
    expect(await hass.config_entries.async_unload(config_entry_setup.entry_id)).to_be(
        True
    )
    expect(config_entry_setup.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def unload_entry_multiple_gateways(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test being able to unload an entry and master gateway gets moved."""

    config_entry = await setup_deconz(hass, aioclient)

    entry2 = MockConfigEntry(
        domain=DOMAIN,
        entry_id="2",
        unique_id="01234E56789B",
        data=config_entry.data | {"host": "2.3.4.5"},
    )
    entry2.add_to_hass(hass)
    register_get_request(aioclient, host="2.3.4.5")
    await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry2.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(entry2.options[CONF_MASTER_GATEWAY]).to_be(True)


@test
async def unload_entry_multiple_gateways_parallel(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test race condition when unloading multiple config entries in parallel."""

    config_entry = await setup_deconz(hass, aioclient)

    entry2 = MockConfigEntry(
        domain=DOMAIN,
        entry_id="2",
        unique_id="01234E56789B",
        data=config_entry.data | {"host": "2.3.4.5"},
    )
    entry2.add_to_hass(hass)
    register_get_request(aioclient, host="2.3.4.5")
    await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry2.state).to_be(ConfigEntryState.LOADED)

    await asyncio.gather(
        hass.config_entries.async_unload(config_entry.entry_id),
        hass.config_entries.async_unload(entry2.entry_id),
    )

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(entry2.state).to_be(ConfigEntryState.NOT_LOADED)
