"""Tryke fixtures for Fritz!Tools tests."""

from collections.abc import Generator
from copy import deepcopy
import logging
from typing import Any
from unittest.mock import MagicMock, patch

from fritzconnection.lib.fritzhosts import FritzHosts
from fritzconnection.lib.fritzstatus import FritzStatus
from tryke import Depends, fixture

from homeassistant.components.fritz.coordinator import FritzConnectionCached

from .const import (
    MOCK_FB_SERVICES,
    MOCK_HOST_ATTRIBUTES_DATA,
    MOCK_MESH_DATA,
    MOCK_MODELNAME,
    MOCK_STATUS_CONNECTION_DATA,
)

from tests.hass_fixtures import mock_network

LOGGER = logging.getLogger(__name__)


class FritzServiceMock:
    """Service mocking."""

    def __init__(self, actions: list[str]) -> None:
        """Init Service mock."""
        self.actions = actions


class FritzConnectionMock:
    """FritzConnection mocking."""

    def __init__(self, fc_data: dict[str, dict[str, Any]]) -> None:
        """Init Mocking class."""
        self._fc_data: dict[str, dict[str, Any]]
        self.services: dict[str, FritzServiceMock]

        self._call_cache: dict[str, dict[str, Any]] = {}
        self.modelname = MOCK_MODELNAME
        self._side_effect: Exception | None = None

        self._service_normalization(fc_data)

    def _service_normalization(self, fc_data: dict[str, dict[str, Any]]) -> None:
        """Normalize service name."""
        self._fc_data = deepcopy(fc_data)
        self.services = {
            service.replace(":", ""): FritzServiceMock(list(actions.keys()))
            for service, actions in fc_data.items()
        }

    def call_action_side_effect(self, side_effect: Exception | None) -> None:
        """Set or unset a side_effect for call_action."""
        self._side_effect = side_effect

    def override_services(self, fc_data: dict[str, dict[str, Any]]) -> None:
        """Override services data."""
        self._service_normalization(fc_data)

    def clear_cache(self) -> None:
        """Mock clear_cache method."""
        return FritzConnectionCached.clear_cache(self)

    def call_action(self, service: str, action: str, **kwargs: Any) -> Any:
        """Simulate TR-064 call with service name normalization."""
        if self._side_effect:
            raise self._side_effect

        normalized = service
        if service not in self._fc_data:
            if (
                (":" in service and (alt := service.replace(":", "")) in self._fc_data)
                or (alt := f"{service}1") in self._fc_data
                or (alt := f"{service}:1") in self._fc_data
                or (
                    service.endswith("1")
                    and ":" not in service
                    and (alt := f"{service[:-1]}:1") in self._fc_data
                )
            ):
                normalized = alt

        action_data = self._fc_data.get(normalized, {}).get(action, {})
        if kwargs:
            if (index := kwargs.get("NewIndex")) is None:
                index = next(iter(kwargs.values()))
            if isinstance(action_data, dict) and index in action_data:
                return action_data[index]

        return action_data


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@fixture
def fc_data() -> dict[str, dict[str, Any]]:
    """Fixture for default fc_data."""
    return deepcopy(MOCK_FB_SERVICES)


@fixture
def fc_class_mock(
    fc_data: dict[str, dict[str, Any]] = Depends(fc_data),
) -> Generator[MagicMock]:
    """Fixture that sets up a mocked FritzConnection class."""
    with patch(
        "homeassistant.components.fritz.coordinator.FritzConnectionCached",
        autospec=True,
    ) as result:
        result.return_value = FritzConnectionMock(fc_data)
        yield result


@fixture
def fh_class_mock() -> Generator[type[FritzHosts]]:
    """Fixture that sets up a mocked FritzHosts class."""
    with (
        patch(
            "homeassistant.components.fritz.coordinator.FritzHosts",
            new=FritzHosts,
        ) as result,
        patch.object(
            FritzHosts,
            "get_mesh_topology",
            MagicMock(return_value=MOCK_MESH_DATA),
        ),
        patch.object(
            FritzHosts,
            "get_hosts_attributes",
            MagicMock(return_value=MOCK_HOST_ATTRIBUTES_DATA),
        ),
    ):
        yield result


@fixture
def fs_class_mock() -> Generator[type[FritzStatus]]:
    """Fixture that sets up a mocked FritzStatus class."""
    with (
        patch(
            "homeassistant.components.fritz.coordinator.FritzStatus",
            new=FritzStatus,
        ) as result,
        patch.object(
            FritzStatus,
            "get_default_connection_service",
            MagicMock(return_value=MOCK_STATUS_CONNECTION_DATA),
        ),
        patch.object(FritzStatus, "get_monitor_data", MagicMock(return_value={})),
        patch.object(
            FritzStatus, "get_cpu_temperatures", MagicMock(return_value=[42, 38])
        ),
        patch.object(FritzStatus, "has_wan_enabled", True),
    ):
        yield result
