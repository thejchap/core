"""Test the discovery flow helper."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, call, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers import discovery_flow, json as json_helper
from homeassistant.helpers.discovery_flow import DiscoveryKey
from homeassistant.util import json as json_util

from tests.hass_fixtures import hass


@fixture
def mock_flow_init(hass: HomeAssistant = Depends(hass)) -> Generator[AsyncMock]:
    """Mock hass.config_entries.flow.async_init."""
    with patch.object(
        hass.config_entries.flow, "async_init", return_value=AsyncMock()
    ) as mock_init:
        yield mock_init


@test.cases(
    test.case("no_discovery_key", discovery_key=None, context={}),
    test.case(
        "string_key",
        discovery_key=DiscoveryKey(domain="test", key="string_key", version=1),
        context={
            "discovery_key": DiscoveryKey(domain="test", key="string_key", version=1)
        },
    ),
    test.case(
        "tuple_key",
        discovery_key=DiscoveryKey(domain="test", key=("one", "two"), version=1),
        context={
            "discovery_key": DiscoveryKey(domain="test", key=("one", "two"), version=1)
        },
    ),
)
async def async_create_flow(
    discovery_key: DiscoveryKey | None,
    context: dict[str, Any],
    hass: HomeAssistant = Depends(hass),
    mock_flow_init: AsyncMock = Depends(mock_flow_init),
) -> None:
    """Test we can create a flow."""
    discovery_flow.async_create_flow(
        hass,
        "hue",
        {"source": config_entries.SOURCE_HOMEKIT},
        {"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        discovery_key=discovery_key,
    )
    expect(mock_flow_init.mock_calls).to_equal(
        [
            call(
                "hue",
                context={"source": "homekit"} | context,
                data={"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
            )
        ]
    )


@test
async def async_create_flow_deferred_until_started(
    hass: HomeAssistant = Depends(hass),
    mock_flow_init: AsyncMock = Depends(mock_flow_init),
) -> None:
    """Test flows are deferred until started."""
    hass.set_state(CoreState.stopped)
    discovery_flow.async_create_flow(
        hass,
        "hue",
        {"source": config_entries.SOURCE_HOMEKIT},
        {"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
    )
    expect(bool(mock_flow_init.mock_calls)).to_be(False)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    expect(mock_flow_init.mock_calls).to_equal(
        [
            call(
                "hue",
                context={"source": "homekit"},
                data={"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
            )
        ]
    )


@test
async def async_create_flow_checks_existing_flows_after_startup(
    hass: HomeAssistant = Depends(hass),
    mock_flow_init: AsyncMock = Depends(mock_flow_init),
) -> None:
    """Test existing flows prevent an identical ones from being after startup."""
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    with patch(
        "homeassistant.config_entries.ConfigEntriesFlowManager.async_has_matching_discovery_flow",
        return_value=True,
    ):
        discovery_flow.async_create_flow(
            hass,
            "hue",
            {"source": config_entries.SOURCE_HOMEKIT},
            {"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        )
        expect(bool(mock_flow_init.mock_calls)).to_be(False)


@test
async def async_create_flow_checks_existing_flows_before_startup(
    hass: HomeAssistant = Depends(hass),
    mock_flow_init: AsyncMock = Depends(mock_flow_init),
) -> None:
    """Test existing flows prevent an identical ones from being created before startup."""
    hass.set_state(CoreState.stopped)
    for _ in range(2):
        discovery_flow.async_create_flow(
            hass,
            "hue",
            {"source": config_entries.SOURCE_HOMEKIT},
            {"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        )
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    expect(mock_flow_init.mock_calls).to_equal(
        [
            call(
                "hue",
                context={"source": "homekit"},
                data={"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
            )
        ]
    )


@test
async def async_create_flow_does_nothing_after_stop(
    hass: HomeAssistant = Depends(hass),
    mock_flow_init: AsyncMock = Depends(mock_flow_init),
) -> None:
    """Test we no longer create flows when hass is stopping."""
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    hass.set_state(CoreState.stopping)
    mock_flow_init.reset_mock()
    discovery_flow.async_create_flow(
        hass,
        "hue",
        {"source": config_entries.SOURCE_HOMEKIT},
        {"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
    )
    expect(len(mock_flow_init.mock_calls)).to_equal(0)


@test.cases(
    test.case("string_key", key="test"),
    test.case("tuple_key", key=("blah", "bleh")),
)
def discovery_key_serialize_deserialize(key: str | tuple[str]) -> None:
    """Test serialize and deserialize discovery key."""
    discovery_key_1 = discovery_flow.DiscoveryKey(
        domain="test_domain", key=key, version=1
    )
    serialized = json_helper.json_dumps(discovery_key_1)
    expect(
        discovery_flow.DiscoveryKey.from_json_dict(json_util.json_loads(serialized))
    ).to_equal(discovery_key_1)
