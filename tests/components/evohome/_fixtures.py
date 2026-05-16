"""Tryke fixtures and helpers for the evohome tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import timedelta, timezone
from http import HTTPMethod
from typing import Any
from unittest.mock import MagicMock, patch

from evohomeasync2 import ControlSystem, EvohomeClient, HotWater, Zone
from evohomeasync2.auth import AbstractTokenManager, Auth
from homeassistant.components.evohome.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.json import JsonArrayType, JsonObjectType

from .const import ACCESS_TOKEN, REFRESH_TOKEN, SESSION_ID, USERNAME

from tests.common import load_json_array_fixture, load_json_object_fixture


def user_account_config_fixture(install: str) -> JsonObjectType:
    """Load JSON for the config of a user's account."""
    try:
        return load_json_object_fixture(f"{install}/user_account.json", DOMAIN)
    except FileNotFoundError:
        return load_json_object_fixture("default/user_account.json", DOMAIN)


def user_locations_config_fixture(install: str) -> JsonArrayType:
    """Load JSON for the config of a user's installation (a list of locations)."""
    return load_json_array_fixture(f"{install}/user_locations.json", DOMAIN)


def location_status_fixture(install: str, loc_id: str | None = None) -> JsonObjectType:
    """Load JSON for the status of a specific location."""
    if loc_id is None:
        _install = load_json_array_fixture(f"{install}/user_locations.json", DOMAIN)
        loc_id = _install[0]["locationInfo"]["locationId"]  # type: ignore[assignment, call-overload, index]
    return load_json_object_fixture(f"{install}/status_{loc_id}.json", DOMAIN)


def dhw_schedule_fixture(install: str, dhw_id: str | None = None) -> JsonObjectType:
    """Load JSON for the schedule of a domesticHotWater zone."""
    try:
        return load_json_object_fixture(f"{install}/schedule_{dhw_id}.json", DOMAIN)
    except FileNotFoundError:
        return load_json_object_fixture("default/schedule_dhw.json", DOMAIN)


def zone_schedule_fixture(install: str, zon_id: str | None = None) -> JsonObjectType:
    """Load JSON for the schedule of a temperatureZone zone."""
    try:
        return load_json_object_fixture(f"{install}/schedule_{zon_id}.json", DOMAIN)
    except FileNotFoundError:
        return load_json_object_fixture("default/schedule_zone.json", DOMAIN)


def mock_post_request(install: str) -> Callable:
    """Obtain an access token via a POST to the vendor's web API."""

    async def post_request(
        self: AbstractTokenManager, url: str, /, **kwargs: Any
    ) -> JsonArrayType | JsonObjectType:
        if "Token" in url:
            return {
                "access_token": f"new_{ACCESS_TOKEN}",
                "token_type": "bearer",
                "expires_in": 1800,
                "refresh_token": f"new_{REFRESH_TOKEN}",
            }

        if "session" in url:
            return {"sessionId": f"new_{SESSION_ID}"}

        raise AssertionError(f"Unexpected request: {HTTPMethod.POST} {url}")

    return post_request


def mock_make_request(install: str) -> Callable:
    """Return a get method for a specified installation."""

    async def make_request(
        self: Auth, method: HTTPMethod, url: str, **kwargs: Any
    ) -> JsonArrayType | JsonObjectType:
        if method != HTTPMethod.GET:
            raise AssertionError(f"Unmocked method: {method} {url}")

        await self._headers()

        if url == "accountInfo":
            return {}

        if url.startswith("locations/"):
            return []

        if url == "userAccount":
            return user_account_config_fixture(install)

        if url.startswith("location/"):
            if "installationInfo" in url:
                return user_locations_config_fixture(install)
            if "status" in url:
                return location_status_fixture(install)

        elif "schedule" in url:
            if url.startswith("domesticHotWater"):
                return dhw_schedule_fixture(install, url[16:23])
            if url.startswith("temperatureZone"):
                return zone_schedule_fixture(install, url[16:23])

        raise AssertionError(f"Unexpected request: {HTTPMethod.GET} {url}")

    return make_request


def _default_config() -> dict[str, str]:
    """Return a default/minimal configuration."""
    return {
        CONF_USERNAME: USERNAME,
        CONF_PASSWORD: "password",
    }


@asynccontextmanager
async def setup_evohome(
    hass: HomeAssistant,
    install: str = "default",
    config: dict[str, str] | None = None,
) -> AsyncGenerator[MagicMock]:
    """Set up the evohome integration and yield its mock client.

    The class is mocked here to check the client was instantiated with the correct args.
    """
    if config is None:
        config = _default_config()

    loc_idx: int = config.get("location_idx", 0)  # type: ignore[assignment]

    try:
        locn = user_locations_config_fixture(install)[loc_idx]
    except IndexError:
        if loc_idx == 0:
            raise
        locn = user_locations_config_fixture(install)[0]

    utc_offset: int = locn["locationInfo"]["timeZone"]["currentOffsetMinutes"]  # type: ignore[assignment, call-overload, index]
    dt_util.set_default_time_zone(timezone(timedelta(minutes=utc_offset)))

    with (
        patch("homeassistant.components.evohome.ec2.EvohomeClient") as mock_client,
        patch(
            "evohomeasync2.auth.CredentialsManagerBase._post_request",
            mock_post_request(install),
        ),
        patch("_evohome.auth.AbstractAuth._make_request", mock_make_request(install)),
    ):
        evo: EvohomeClient | None = None

        def evohome_client(*args, **kwargs) -> EvohomeClient:
            nonlocal evo
            evo = EvohomeClient(*args, **kwargs)
            return evo

        mock_client.side_effect = evohome_client

        assert await async_setup_component(hass, DOMAIN, {DOMAIN: config})
        await hass.async_block_till_done()

        mock_client.assert_called_once()

        assert isinstance(evo, EvohomeClient)
        assert evo._token_manager.client_id == config[CONF_USERNAME]
        assert evo._token_manager._secret == config[CONF_PASSWORD]

        assert evo.user_account

        mock_client.return_value = evo
        yield mock_client


def get_entity_id_helper(
    entity_registry: er.EntityRegistry,
) -> Callable[[Platform, str], str]:
    """Return a helper to lookup an entity_id from platform and unique_id."""

    def get_entity_id(platform: Platform, unique_id: str) -> str:
        entity = entity_registry.async_get_entity_id(platform, DOMAIN, unique_id)
        assert entity is not None, (
            f"Entity not found for platform={platform}: {unique_id}"
        )
        return entity

    return get_entity_id


@dataclass
class EvoSetup:
    """Bundle of values produced by ``setup_evo_for_test``."""

    mock_client: MagicMock
    entity_id: Callable[[Platform, str], str]
    ctl_id: str
    zone_id: str
    dhw_id: str | None


@asynccontextmanager
async def setup_evo_for_test(
    hass: HomeAssistant,
    install: str,
    entity_registry: er.EntityRegistry,
) -> AsyncGenerator[EvoSetup]:
    """Set up evohome for a tryke test and yield resolved entity_ids.

    Equivalent to the legacy pytest ``evohome`` / ``ctl_id`` / ``zone_id``
    / ``dhw_id`` fixture chain rolled into a single async context manager
    so each tryke test can drive the install parametrization inline.
    """
    entity_id_fn = get_entity_id_helper(entity_registry)

    async with setup_evohome(hass, install=install) as mock_client:
        evo: EvohomeClient = mock_client.return_value
        tcs: ControlSystem = evo.tcs

        ctl_entity_id = entity_id_fn(Platform.CLIMATE, tcs.id)

        zone: Zone = tcs.zones[0]
        zone_unique_id = f"{zone.id}z" if zone.id == tcs.id else zone.id
        zone_entity_id = entity_id_fn(Platform.CLIMATE, zone_unique_id)

        dhw: HotWater | None = tcs.hotwater
        dhw_entity_id = (
            entity_id_fn(Platform.WATER_HEATER, dhw.id) if dhw is not None else None
        )

        yield EvoSetup(
            mock_client=mock_client,
            entity_id=entity_id_fn,
            ctl_id=ctl_entity_id,
            zone_id=zone_entity_id,
            dhw_id=dhw_entity_id,
        )
