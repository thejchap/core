"""Tryke fixtures for mobile_app tests (ported from conftest.py)."""

from http import HTTPStatus
from typing import Any

from aiohttp.test_utils import TestClient
from tryke import Depends, fixture

from homeassistant.components.mobile_app.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .const import REGISTER, REGISTER_CLEARTEXT

from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
)


@fixture
async def setup_ws(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Configure the websocket_api component."""
    assert await async_setup_component(hass, "repairs", {})
    assert await async_setup_component(hass, "websocket_api", {})
    await hass.async_block_till_done()


@fixture
async def webhook_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    _setup_ws: None = Depends(setup_ws),
) -> TestClient:
    """Provide an authenticated client for mobile_app to use."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()
    return await hass_client()


@fixture
async def create_registrations(
    hass: HomeAssistant = Depends(hass_fixture),
    webhook_client: TestClient = Depends(webhook_client),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return two new registrations."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    enc_reg = await webhook_client.post("/api/mobile_app/registrations", json=REGISTER)

    assert enc_reg.status == HTTPStatus.CREATED
    enc_reg_json = await enc_reg.json()

    clear_reg = await webhook_client.post(
        "/api/mobile_app/registrations", json=REGISTER_CLEARTEXT
    )

    assert clear_reg.status == HTTPStatus.CREATED
    clear_reg_json = await clear_reg.json()

    await hass.async_block_till_done()

    return (enc_reg_json, clear_reg_json)
