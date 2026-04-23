"""Tryke fixtures for NRGkick tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from nrgkick_api import ConnectorType, GridPhases
from tryke import Depends, fixture

from homeassistant.components.nrgkick.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_async_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf to prevent cross-test teardown issues."""
    from zeroconf import DNSCache, Zeroconf
    from zeroconf.asyncio import AsyncZeroconf

    with patch(
        "homeassistant.components.zeroconf.HaAsyncZeroconf", spec=AsyncZeroconf
    ) as mock_aiozc:
        zc = mock_aiozc.return_value
        zc.async_unregister_service = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.zeroconf = Mock(spec=Zeroconf)
        zc.zeroconf.async_wait_for_start = AsyncMock()
        zc.zeroconf.cache = DNSCache()
        zc.zeroconf.done = False
        zc.async_close = AsyncMock()
        zc.ha_async_close = AsyncMock()
        yield zc


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.nrgkick.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_info_data() -> dict[str, Any]:
    """Mock device info data."""
    res = load_json_object_fixture("info.json", DOMAIN)
    res["connector"]["type"] = ConnectorType.TYPE2
    res["grid"]["phases"] = GridPhases.L1_L2_L3
    return res


@fixture
def mock_control_data() -> dict[str, Any]:
    """Mock control data."""
    return load_json_object_fixture("control.json", DOMAIN)


@fixture
def mock_values_data() -> dict[str, Any]:
    """Mock values data."""
    return load_json_object_fixture("values_sensor.json", DOMAIN)


@fixture
def mock_nrgkick_api(
    mock_info_data_: dict[str, Any] = Depends(mock_info_data),
    mock_control_data_: dict[str, Any] = Depends(mock_control_data),
    mock_values_data_: dict[str, Any] = Depends(mock_values_data),
) -> Generator[AsyncMock]:
    """Mock the NRGkick API client and patch it where used."""
    with (
        patch(
            "homeassistant.components.nrgkick.NRGkickAPI",
            autospec=True,
        ) as mock_api_cls,
        patch(
            "homeassistant.components.nrgkick.config_flow.NRGkickAPI",
            new=mock_api_cls,
        ),
    ):
        api = mock_api_cls.return_value
        api.test_connection.return_value = True
        api.get_info.return_value = mock_info_data_
        api.get_control.return_value = mock_control_data_
        api.get_values.return_value = mock_values_data_
        api.set_current.return_value = 16.0
        api.set_charge_pause.return_value = 0
        api.set_energy_limit.return_value = 0
        api.set_phase_count.return_value = 3
        yield api


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="NRGkick Test",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_pass",
        },
        entry_id="test_entry_id",
        unique_id="TEST123456",
    )
