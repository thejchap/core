"""Test init of Tractive integration."""

from typing import Any
from unittest.mock import AsyncMock, patch

from aiotractive.exceptions import TractiveError, UnauthorizedError
from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.tractive.const import (
    ATTR_DAILY_GOAL,
    ATTR_MINUTES_ACTIVE,
    ATTR_MINUTES_DAY_SLEEP,
    ATTR_MINUTES_NIGHT_SLEEP,
    ATTR_MINUTES_REST,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import init_integration
from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_tractive_client as mock_tractive_client_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    caplog as caplog_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def setup_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test a successful setup entry."""
    await init_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def unload_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test successful unload of entry."""
    await init_integration(hass, mock_config_entry)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    with patch("homeassistant.components.tractive.TractiveClient.unsubscribe"):
        expect(
            await hass.config_entries.async_unload(mock_config_entry.entry_id)
        ).to_be_truthy()
        await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(hass.data.get(DOMAIN)).to_be_falsy()


@test.cases(
    test.case(
        "authenticate_unauthorized",
        method="authenticate",
        exc=UnauthorizedError,
        entry_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "authenticate_tractive_error",
        method="authenticate",
        exc=TractiveError,
        entry_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "trackable_objects_tractive_error",
        method="trackable_objects",
        exc=TractiveError,
        entry_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_failed(
    method: str,
    exc: type[Exception],
    entry_state: ConfigEntryState,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test for setup failure."""
    getattr(mock_tractive_client, method).side_effect = exc

    await init_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(entry_state)


@test
async def config_not_ready(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test for setup failure if the tracker_details doesn't contain '_id'."""
    mock_tractive_client.tracker.return_value.details.return_value.pop("_id")

    await init_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def trackable_without_details(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    caplog: Any = Depends(caplog_fx),
) -> None:
    """Test a successful setup entry."""
    mock_tractive_client.trackable_objects.return_value[0].details.return_value = {
        "device_id": "xyz098"
    }

    await init_integration(hass, mock_config_entry)

    expect(
        "Tracker xyz098 has no details and will be skipped. This happens for shared trackers"
        in caplog.text
    ).to_be_truthy()
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def trackable_without_device_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test a successful setup entry."""
    mock_tractive_client.trackable_objects.return_value[0].details.return_value = {
        "device_id": None
    }

    await init_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def unsubscribe_on_ha_stop(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test unsuscribe when HA stops."""
    await init_integration(hass, mock_config_entry)

    with patch(
        "homeassistant.components.tractive.TractiveClient.unsubscribe"
    ) as mock_unsuscribe:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()

    expect(mock_unsuscribe.called).to_be_truthy()


@test.skip(
    "translation-loading bug; sensor entity not registered without translations/en.json"
)
async def server_unavailable() -> None:
    """Test states of the sensor (broken upstream)."""


@test.cases(
    test.case("none", sleep_data=None),
    test.case("empty", sleep_data={}),
    test.case("unexpected", sleep_data={"unexpected": 123}),
)
async def missing_sleep_data(
    sleep_data: dict[str, Any] | None,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test for missing sleep data."""
    event = {"petId": "pet_id_123", "sleep": sleep_data}

    await init_integration(hass, mock_config_entry)

    with patch(
        "homeassistant.components.tractive.async_dispatcher_send"
    ) as async_dispatcher_send_mock:
        mock_tractive_client.send_health_overview_event(mock_config_entry, event)

    expect(async_dispatcher_send_mock.call_count).to_equal(1)
    payload = async_dispatcher_send_mock.mock_calls[0][1][2]
    expect(payload[ATTR_MINUTES_DAY_SLEEP]).to_be(None)
    expect(payload[ATTR_MINUTES_NIGHT_SLEEP]).to_be(None)
    expect(payload[ATTR_MINUTES_REST]).to_be(None)


@test.cases(
    test.case("none", activity_data=None),
    test.case("empty", activity_data={}),
    test.case("unexpected", activity_data={"unexpected": 123}),
)
async def missing_activity_data(
    activity_data: dict[str, Any] | None,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test for missing activity data."""
    event = {"petId": "pet_id_123", "activity": activity_data}

    await init_integration(hass, mock_config_entry)

    with patch(
        "homeassistant.components.tractive.async_dispatcher_send"
    ) as async_dispatcher_send_mock:
        mock_tractive_client.send_health_overview_event(mock_config_entry, event)

    expect(async_dispatcher_send_mock.call_count).to_equal(1)
    payload = async_dispatcher_send_mock.mock_calls[0][1][2]
    expect(payload[ATTR_DAILY_GOAL]).to_be(None)
    expect(payload[ATTR_MINUTES_ACTIVE]).to_be(None)


@test.cases(
    test.case("activity_label", sensor="activity_label"),
    test.case("calories", sensor="calories"),
    test.case("sleep_label", sensor="sleep_label"),
)
async def remove_unsupported_sensor_entity(
    sensor: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_tractive_client: AsyncMock = Depends(mock_tractive_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test removing unsupported sensor entity."""
    entity_id = f"sensor.test_pet_{sensor}"
    mock_config_entry.add_to_hass(hass)

    entity_registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        f"pet_id_123_{sensor}",
        suggested_object_id=entity_id.rsplit(".", maxsplit=1)[-1],
        config_entry=mock_config_entry,
    )

    await init_integration(hass, mock_config_entry)

    expect(entity_registry.async_get(entity_id)).to_be(None)
