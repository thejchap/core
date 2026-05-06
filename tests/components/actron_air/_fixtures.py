"""Tryke fixtures for the Actron Air integration."""

import asyncio
from collections.abc import Generator
import json
from unittest.mock import AsyncMock, MagicMock, patch

from actron_neo_api.models.auth import ActronAirDeviceCode, ActronAirUserInfo
from actron_neo_api.models.settings import ActronAirUserAirconSettings
from actron_neo_api.models.status import ActronAirStatus
from actron_neo_api.models.system import ActronAirACSystem, ActronAirSystemInfo
from tryke import fixture

from homeassistant.components.actron_air.const import DOMAIN
from homeassistant.const import CONF_API_TOKEN

from tests.common import MockConfigEntry, load_fixture


@fixture
def mock_actron_api() -> Generator[AsyncMock]:
    """Mock the Actron Air API class."""
    with (
        patch(
            "homeassistant.components.actron_air.ActronAirAPI",
            autospec=True,
        ) as mock_api,
        patch(
            "homeassistant.components.actron_air.config_flow.ActronAirAPI",
            new=mock_api,
        ),
        patch.object(ActronAirACSystem, "set_system_mode", new_callable=AsyncMock),
        patch.object(
            ActronAirUserAirconSettings, "set_away_mode", new_callable=AsyncMock
        ),
        patch.object(
            ActronAirUserAirconSettings,
            "set_continuous_mode",
            new_callable=AsyncMock,
        ),
        patch.object(
            ActronAirUserAirconSettings, "set_quiet_mode", new_callable=AsyncMock
        ),
        patch.object(
            ActronAirUserAirconSettings, "set_turbo_mode", new_callable=AsyncMock
        ),
        patch.object(
            ActronAirUserAirconSettings, "set_temperature", new_callable=AsyncMock
        ),
        patch.object(
            ActronAirUserAirconSettings, "set_fan_mode", new_callable=AsyncMock
        ),
    ):
        api = mock_api.return_value

        api.request_device_code.return_value = ActronAirDeviceCode(
            device_code="test_device_code",
            user_code="ABC123",
            verification_uri="https://example.com",
            verification_uri_complete="https://example.com/device",
            expires_in=1800,
            interval=5,
        )

        async def slow_poll_for_token(device_code: str) -> dict[str, str]:
            await asyncio.sleep(0.1)
            return {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
            }

        api.poll_for_token = slow_poll_for_token

        api.get_user_info = AsyncMock(
            return_value=ActronAirUserInfo(id="test_user_id", email="test@example.com")
        )

        api.refresh_token_value = "test_refresh_token"

        api.get_ac_systems = AsyncMock(
            return_value=[ActronAirSystemInfo(serial="123456")]
        )

        status = ActronAirStatus.model_validate(
            json.loads(load_fixture("status.json", DOMAIN))
        )
        status.set_api(api)

        api.state_manager = MagicMock()
        api.state_manager.get_status.return_value = status

        yield api


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        data={CONF_API_TOKEN: "test_refresh_token"},
        unique_id="test_user_id",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock async_setup_entry."""
    with patch(
        "homeassistant.components.actron_air.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
