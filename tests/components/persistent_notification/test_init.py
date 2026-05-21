"""The tests for the persistent notification component."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import persistent_notification as pn
from homeassistant.components.websocket_api import TYPE_RESULT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
)
from tests.typing import WebSocketGenerator


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Set up the persistent_notification integration (mirrors autouse conftest)."""
    expect(await async_setup_component(hass, pn.DOMAIN, {})).to_be(True)
    return hass


@test
async def create(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creating notification without title or notification id."""
    notifications = pn._async_get_or_create_notifications(hass)
    expect(len(hass.states.async_entity_ids(pn.DOMAIN))).to_equal(0)
    expect(len(notifications)).to_equal(0)

    pn.async_create(hass, "Hello World 2", title="2 beers")
    expect(len(notifications)).to_equal(1)

    notification = notifications[list(notifications)[0]]
    expect(notification["message"]).to_equal("Hello World 2")
    expect(notification["title"]).to_equal("2 beers")
    expect(notification["created_at"]).not_.to_be(None)


@test
async def create_notification_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure overwrites existing notification with same id."""
    notifications = pn._async_get_or_create_notifications(hass)
    expect(len(hass.states.async_entity_ids(pn.DOMAIN))).to_equal(0)
    expect(len(notifications)).to_equal(0)

    pn.async_create(hass, "test", notification_id="Beer 2")

    expect(len(notifications)).to_equal(1)
    notification = notifications[list(notifications)[0]]

    expect(notification["message"]).to_equal("test")
    expect(notification["title"]).to_be(None)

    pn.async_create(hass, "test 2", notification_id="Beer 2")

    # We should have overwritten old one
    notification = notifications[list(notifications)[0]]

    expect(notification["message"]).to_equal("test 2")


@test
async def dismiss_notification(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure removal of specific notification."""
    notifications = pn._async_get_or_create_notifications(hass)
    expect(len(notifications)).to_equal(0)

    pn.async_create(hass, "test", notification_id="Beer 2")

    expect(len(notifications)).to_equal(1)
    pn.async_dismiss(hass, notification_id="Does Not Exist")

    expect(len(notifications)).to_equal(1)

    pn.async_dismiss(hass, notification_id="Beer 2")

    expect(len(notifications)).to_equal(0)


@test
async def dismiss_all_notifications(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure removal of all notifications."""
    notifications = pn._async_get_or_create_notifications(hass)
    expect(len(notifications)).to_equal(0)

    pn.async_create(hass, "test", notification_id="Beer 2")
    pn.async_create(hass, "test", notification_id="Beer 3")
    pn.async_create(hass, "test", notification_id="Beer 4")
    pn.async_create(hass, "test", notification_id="Beer 5")

    expect(len(notifications)).to_equal(4)
    pn.async_dismiss_all(hass)

    expect(len(notifications)).to_equal(0)


@test
async def ws_get_notifications(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test websocket endpoint for retrieving persistent notifications."""
    await async_setup_component(hass, pn.DOMAIN, {})

    client = await hass_ws_client(hass)

    await client.send_json({"id": 5, "type": "persistent_notification/get"})
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    notifications = msg["result"]
    expect(len(notifications)).to_equal(0)

    # Create
    pn.async_create(hass, "test", notification_id="Beer 2")
    await client.send_json({"id": 6, "type": "persistent_notification/get"})
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(6)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    notifications = msg["result"]
    expect(len(notifications)).to_equal(1)
    notification = notifications[0]
    expect(notification["notification_id"]).to_equal("Beer 2")
    expect(notification["message"]).to_equal("test")
    expect(notification["title"]).to_be(None)
    expect(notification["created_at"]).not_.to_be(None)

    # Dismiss
    pn.async_dismiss(hass, "Beer 2")
    await client.send_json({"id": 8, "type": "persistent_notification/get"})
    msg = await client.receive_json()
    notifications = msg["result"]
    expect(len(notifications)).to_equal(0)


@test
async def ws_get_subscribe(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test websocket subscribe endpoint for retrieving persistent notifications."""
    await async_setup_component(hass, pn.DOMAIN, {})

    client = await hass_ws_client(hass)

    await client.send_json({"id": 5, "type": "persistent_notification/subscribe"})
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)

    msg = await client.receive_json()
    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal("event")
    expect(msg["event"]).not_.to_be(None)
    event = msg["event"]
    expect(event["type"]).to_equal("current")
    expect(event["notifications"]).to_equal({})

    # Create
    pn.async_create(hass, "test", notification_id="Beer 2")

    msg = await client.receive_json()
    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal("event")
    expect(msg["event"]).not_.to_be(None)
    event = msg["event"]
    expect(event["type"]).to_equal("added")
    notifications = event["notifications"]
    expect(len(notifications)).to_equal(1)
    notification = notifications[list(notifications)[0]]
    expect(notification["notification_id"]).to_equal("Beer 2")
    expect(notification["message"]).to_equal("test")
    expect(notification["title"]).to_be(None)
    expect(notification["created_at"]).not_.to_be(None)

    # Dismiss
    pn.async_dismiss(hass, "Beer 2")
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal("event")
    expect(msg["event"]).not_.to_be(None)
    event = msg["event"]
    expect(event["type"]).to_equal("removed")


@test
async def manual_notification_id_round_trip(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that a manual notification id can be round tripped."""
    notifications = pn._async_get_or_create_notifications(hass)
    expect(len(notifications)).to_equal(0)

    await hass.services.async_call(
        pn.DOMAIN,
        "create",
        {"notification_id": "synology_diskstation_hub_notification", "message": "test"},
        blocking=True,
    )

    expect(len(notifications)).to_equal(1)

    await hass.services.async_call(
        pn.DOMAIN,
        "dismiss",
        {"notification_id": "synology_diskstation_hub_notification"},
        blocking=True,
    )

    expect(len(notifications)).to_equal(0)


@test
async def manual_dismiss_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the dismiss all service."""
    notifications = pn._async_get_or_create_notifications(hass)
    expect(len(notifications)).to_equal(0)

    await hass.services.async_call(
        pn.DOMAIN,
        "create",
        {"notification_id": "Beer 1", "message": "test"},
        blocking=True,
    )

    await hass.services.async_call(
        pn.DOMAIN,
        "create",
        {"notification_id": "Beer 2", "message": "test 2"},
        blocking=True,
    )

    expect(len(notifications)).to_equal(2)

    await hass.services.async_call(
        pn.DOMAIN,
        "dismiss_all",
        None,
        blocking=True,
    )

    expect(len(notifications)).to_equal(0)
