"""Test the motionEye camera web hooks."""

import copy
from http import HTTPStatus
from unittest.mock import AsyncMock, Mock, call, patch

from motioneye_client.const import (
    KEY_CAMERAS,
    KEY_HTTP_METHOD_POST_JSON,
    KEY_ROOT_DIRECTORY,
    KEY_WEB_HOOK_NOTIFICATIONS_ENABLED,
    KEY_WEB_HOOK_NOTIFICATIONS_HTTP_METHOD,
    KEY_WEB_HOOK_NOTIFICATIONS_URL,
    KEY_WEB_HOOK_STORAGE_ENABLED,
    KEY_WEB_HOOK_STORAGE_HTTP_METHOD,
    KEY_WEB_HOOK_STORAGE_URL,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.motioneye.const import (
    ATTR_EVENT_TYPE,
    CONF_WEBHOOK_SET_OVERWRITE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_FILE_STORED,
    EVENT_MOTION_DETECTED,
)
from homeassistant.components.webhook import URL_WEBHOOK_PATH
from homeassistant.const import ATTR_DEVICE_ID, CONF_URL, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.network import NoURLAvailableError
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import (
    TEST_CAMERA,
    TEST_CAMERA_DEVICE_IDENTIFIER,
    TEST_CAMERA_ENTITY_ID,
    TEST_CAMERA_ID,
    TEST_CAMERA_NAME,
    TEST_CAMERAS,
    TEST_CONFIG_ENTRY_ID,
    TEST_URL,
    create_mock_motioneye_client,
    create_mock_motioneye_config_entry,
    setup_mock_motioneye_config_entry,
)

from tests.common import MockConfigEntry, async_capture_events, async_fire_time_changed
from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fx,
    hass as hass_fx,
    hass_client_no_auth as hass_client_no_auth_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


WEB_HOOK_MOTION_DETECTED_QUERY_STRING = (
    "camera_id=%t&changed_pixels=%D&despeckle_labels=%Q&event=%v&fps=%{fps}"
    "&frame_number=%q&height=%h&host=%{host}&motion_center_x=%K&motion_center_y=%L"
    "&motion_height=%J&motion_version=%{ver}&motion_width=%i&noise_level=%N"
    "&threshold=%o&width=%w&src=hass-motioneye&event_type=motion_detected"
)

WEB_HOOK_FILE_STORED_QUERY_STRING = (
    "camera_id=%t&event=%v&file_path=%f&file_type=%n&fps=%{fps}&frame_number=%q"
    "&height=%h&host=%{host}&motion_version=%{ver}&noise_level=%N&threshold=%o&width=%w"
    "&src=hass-motioneye&event_type=file_stored"
)


@test
async def setup_camera_without_webhook(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test a camera with no webhook."""
    client = create_mock_motioneye_client()
    config_entry = await setup_mock_motioneye_config_entry(hass, client=client)

    device = device_registry.async_get_device(
        identifiers={TEST_CAMERA_DEVICE_IDENTIFIER}
    )
    expect(device).not_.to_be_none()

    expected_camera = copy.deepcopy(TEST_CAMERA)
    expected_camera[KEY_WEB_HOOK_NOTIFICATIONS_ENABLED] = True
    expected_camera[KEY_WEB_HOOK_NOTIFICATIONS_HTTP_METHOD] = KEY_HTTP_METHOD_POST_JSON
    expected_camera[KEY_WEB_HOOK_NOTIFICATIONS_URL] = (
        "https://internal.url"
        + URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID])
        + f"?{WEB_HOOK_MOTION_DETECTED_QUERY_STRING}&device_id={device.id}"
    )

    expected_camera[KEY_WEB_HOOK_STORAGE_ENABLED] = True
    expected_camera[KEY_WEB_HOOK_STORAGE_HTTP_METHOD] = KEY_HTTP_METHOD_POST_JSON
    expected_camera[KEY_WEB_HOOK_STORAGE_URL] = (
        "https://internal.url"
        + URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID])
        + f"?{WEB_HOOK_FILE_STORED_QUERY_STRING}&device_id={device.id}"
    )
    expect(client.async_set_camera.call_args).to_equal(
        call(TEST_CAMERA_ID, expected_camera)
    )


@test
async def setup_camera_with_wrong_webhook(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test camera with wrong web hook."""
    wrong_url = "http://wrong-url"

    client = create_mock_motioneye_client()
    cameras = copy.deepcopy(TEST_CAMERAS)
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_NOTIFICATIONS_URL] = wrong_url
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_STORAGE_URL] = wrong_url
    client.async_get_cameras = AsyncMock(return_value=cameras)

    config_entry = create_mock_motioneye_config_entry(hass)
    await setup_mock_motioneye_config_entry(
        hass,
        config_entry=config_entry,
        client=client,
    )
    expect(client.async_set_camera.called).to_be_falsy()

    with patch(
        "homeassistant.components.motioneye.MotionEyeClient",
        return_value=client,
    ):
        hass.config_entries.async_update_entry(
            config_entry, options={CONF_WEBHOOK_SET_OVERWRITE: True}
        )
        await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()

    device = device_registry.async_get_device(
        identifiers={TEST_CAMERA_DEVICE_IDENTIFIER}
    )
    expect(device).not_.to_be_none()

    expected_camera = copy.deepcopy(TEST_CAMERA)
    expected_camera[KEY_WEB_HOOK_NOTIFICATIONS_ENABLED] = True
    expected_camera[KEY_WEB_HOOK_NOTIFICATIONS_HTTP_METHOD] = KEY_HTTP_METHOD_POST_JSON
    expected_camera[KEY_WEB_HOOK_NOTIFICATIONS_URL] = (
        "https://internal.url"
        + URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID])
        + f"?{WEB_HOOK_MOTION_DETECTED_QUERY_STRING}&device_id={device.id}"
    )

    expected_camera[KEY_WEB_HOOK_STORAGE_ENABLED] = True
    expected_camera[KEY_WEB_HOOK_STORAGE_HTTP_METHOD] = KEY_HTTP_METHOD_POST_JSON
    expected_camera[KEY_WEB_HOOK_STORAGE_URL] = (
        "https://internal.url"
        + URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID])
        + f"?{WEB_HOOK_FILE_STORED_QUERY_STRING}&device_id={device.id}"
    )

    expect(client.async_set_camera.call_args).to_equal(
        call(TEST_CAMERA_ID, expected_camera)
    )


@test
async def setup_camera_with_old_webhook(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Verify that webhooks are overwritten if they are from this integration.

    Even if the overwrite option is disabled, verify the behavior is still to
    overwrite incorrect versions of the URL that were set by this integration.

    (To allow the web hook URL to be seamlessly updated in future versions)
    """

    old_url = "http://old-url?src=hass-motioneye"

    client = create_mock_motioneye_client()
    cameras = copy.deepcopy(TEST_CAMERAS)
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_NOTIFICATIONS_URL] = old_url
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_STORAGE_URL] = old_url
    client.async_get_cameras = AsyncMock(return_value=cameras)

    config_entry = create_mock_motioneye_config_entry(hass)
    await setup_mock_motioneye_config_entry(
        hass,
        config_entry=config_entry,
        client=client,
    )
    expect(client.async_set_camera.called).to_be_truthy()

    device = device_registry.async_get_device(
        identifiers={TEST_CAMERA_DEVICE_IDENTIFIER}
    )
    expect(device).not_.to_be_none()

    expected_camera = copy.deepcopy(TEST_CAMERA)
    expected_camera[KEY_WEB_HOOK_NOTIFICATIONS_ENABLED] = True
    expected_camera[KEY_WEB_HOOK_NOTIFICATIONS_HTTP_METHOD] = KEY_HTTP_METHOD_POST_JSON
    expected_camera[KEY_WEB_HOOK_NOTIFICATIONS_URL] = (
        "https://internal.url"
        + URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID])
        + f"?{WEB_HOOK_MOTION_DETECTED_QUERY_STRING}&device_id={device.id}"
    )

    expected_camera[KEY_WEB_HOOK_STORAGE_ENABLED] = True
    expected_camera[KEY_WEB_HOOK_STORAGE_HTTP_METHOD] = KEY_HTTP_METHOD_POST_JSON
    expected_camera[KEY_WEB_HOOK_STORAGE_URL] = (
        "https://internal.url"
        + URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID])
        + f"?{WEB_HOOK_FILE_STORED_QUERY_STRING}&device_id={device.id}"
    )

    expect(client.async_set_camera.call_args).to_equal(
        call(TEST_CAMERA_ID, expected_camera)
    )


@test
async def setup_camera_with_correct_webhook(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Verify that webhooks are not overwritten if they are already correct."""

    client = create_mock_motioneye_client()
    config_entry = create_mock_motioneye_config_entry(
        hass, data={CONF_URL: TEST_URL, CONF_WEBHOOK_ID: "webhook_secret_id"}
    )

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={TEST_CAMERA_DEVICE_IDENTIFIER},
    )

    cameras = copy.deepcopy(TEST_CAMERAS)
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_NOTIFICATIONS_ENABLED] = True
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_NOTIFICATIONS_HTTP_METHOD] = (
        KEY_HTTP_METHOD_POST_JSON
    )
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_NOTIFICATIONS_URL] = (
        "https://internal.url"
        + URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID])
        + f"?{WEB_HOOK_MOTION_DETECTED_QUERY_STRING}&device_id={device.id}"
    )
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_STORAGE_ENABLED] = True
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_STORAGE_HTTP_METHOD] = (
        KEY_HTTP_METHOD_POST_JSON
    )
    cameras[KEY_CAMERAS][0][KEY_WEB_HOOK_STORAGE_URL] = (
        "https://internal.url"
        + URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID])
        + f"?{WEB_HOOK_FILE_STORED_QUERY_STRING}&device_id={device.id}"
    )
    client.async_get_cameras = AsyncMock(return_value=cameras)

    await setup_mock_motioneye_config_entry(
        hass,
        config_entry=config_entry,
        client=client,
    )

    # Webhooks are correctly configured, so no set call should have been made.
    expect(client.async_set_camera.called).to_be_falsy()


@test
async def setup_camera_with_no_home_assistant_urls(
    hass: HomeAssistant = Depends(hass_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Verify setup works without Home Assistant internal/external URLs."""

    client = create_mock_motioneye_client()
    config_entry = create_mock_motioneye_config_entry(hass, data={CONF_URL: TEST_URL})

    with patch(
        "homeassistant.components.motioneye.get_url", side_effect=NoURLAvailableError
    ):
        await setup_mock_motioneye_config_entry(
            hass,
            config_entry=config_entry,
            client=client,
        )

    # Should log a warning ...
    expect(caplog.text).to_contain("Unable to get Home Assistant URL")

    # ... should not set callbacks in the camera ...
    expect(client.async_set_camera.called).to_be_falsy()

    # ... but camera should still be present.
    entity_state = hass.states.get(TEST_CAMERA_ENTITY_ID)
    expect(entity_state).not_.to_be_none()


@test
async def good_query(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test good callbacks."""
    await async_setup_component(hass, "http", {"http": {}})

    client = create_mock_motioneye_client()
    config_entry = await setup_mock_motioneye_config_entry(hass, client=client)

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={TEST_CAMERA_DEVICE_IDENTIFIER},
    )

    data = {
        "one": "1",
        "two": "2",
        ATTR_DEVICE_ID: device.id,
    }
    client = await hass_client_no_auth()

    for event in (EVENT_MOTION_DETECTED, EVENT_FILE_STORED):
        events = async_capture_events(hass, f"{DOMAIN}.{event}")

        resp = await client.post(
            URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
            json={
                **data,
                ATTR_EVENT_TYPE: event,
            },
        )
        expect(resp.status).to_equal(HTTPStatus.OK)

        expect(len(events)).to_equal(1)
        expect(events[0].data).to_equal(
            {
                "name": TEST_CAMERA_NAME,
                "device_id": device.id,
                ATTR_EVENT_TYPE: event,
                CONF_WEBHOOK_ID: config_entry.data[CONF_WEBHOOK_ID],
                **data,
            }
        )


@test
async def bad_query_missing_parameters(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test a query with missing parameters."""
    await async_setup_component(hass, "http", {"http": {}})
    config_entry = await setup_mock_motioneye_config_entry(hass)

    client = await hass_client_no_auth()

    resp = await client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]), json={}
    )
    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)


@test
async def bad_query_no_such_device(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test a correct query with incorrect device."""
    await async_setup_component(hass, "http", {"http": {}})
    config_entry = await setup_mock_motioneye_config_entry(hass)

    client = await hass_client_no_auth()

    resp = await client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_EVENT_TYPE: EVENT_MOTION_DETECTED,
            ATTR_DEVICE_ID: "not-a-real-device",
        },
    )
    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)


@test
async def bad_query_cannot_decode(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test a correct query with incorrect device."""
    await async_setup_component(hass, "http", {"http": {}})
    config_entry = await setup_mock_motioneye_config_entry(hass)

    client = await hass_client_no_auth()

    motion_events = async_capture_events(hass, f"{DOMAIN}.{EVENT_MOTION_DETECTED}")
    storage_events = async_capture_events(hass, f"{DOMAIN}.{EVENT_FILE_STORED}")

    resp = await client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        data=b"this is not json",
    )
    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect(motion_events).to_be_falsy()
    expect(storage_events).to_be_falsy()


@test
async def event_media_data(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test an event with a file path generates media data."""
    await async_setup_component(hass, "http", {"http": {}})

    client = create_mock_motioneye_client()
    config_entry = await setup_mock_motioneye_config_entry(hass, client=client)

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={TEST_CAMERA_DEVICE_IDENTIFIER},
    )

    hass_client = await hass_client_no_auth()

    events = async_capture_events(hass, f"{DOMAIN}.{EVENT_FILE_STORED}")

    client.get_movie_url = Mock(return_value="http://movie-url")
    client.get_image_url = Mock(return_value="http://image-url")

    # Test: Movie storage.
    client.is_file_type_image = Mock(return_value=False)
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/one",
            "file_type": "8",
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(len(events)).to_equal(1)
    expect(events[-1].data["file_url"]).to_equal("http://movie-url")
    expect(events[-1].data["media_content_id"]).to_equal(
        f"media-source://motioneye/{TEST_CONFIG_ENTRY_ID}#{device.id}#movies#/dir/one"
    )
    expect(client.get_movie_url.call_args).to_equal(call(TEST_CAMERA_ID, "/dir/one"))

    # Test: Image storage.
    client.is_file_type_image = Mock(return_value=True)
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/two",
            "file_type": "4",
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(len(events)).to_equal(2)
    expect(events[-1].data["file_url"]).to_equal("http://image-url")
    expect(events[-1].data["media_content_id"]).to_equal(
        f"media-source://motioneye/{TEST_CONFIG_ENTRY_ID}#{device.id}#images#/dir/two"
    )
    expect(client.get_image_url.call_args).to_equal(call(TEST_CAMERA_ID, "/dir/two"))

    # Test: Invalid file type.
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/three",
            "file_type": "NOT_AN_INT",
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(len(events)).to_equal(3)
    expect(events[-1].data).not_.to_contain("file_url")
    expect(events[-1].data).not_.to_contain("media_content_id")

    # Test: Different file path.
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": "/var/random",
            "file_type": "8",
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(len(events)).to_equal(4)
    expect(events[-1].data).not_.to_contain("file_url")
    expect(events[-1].data).not_.to_contain("media_content_id")

    # Test: Not a loaded motionEye config entry.
    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    wrong_device = device_registry.async_get_or_create(
        config_entry_id=other_config_entry.entry_id, identifiers={("motioneye", "a_1")}
    )
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: wrong_device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": "/var/random",
            "file_type": "8",
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(len(events)).to_equal(5)
    expect(events[-1].data).not_.to_contain("file_url")
    expect(events[-1].data).not_.to_contain("media_content_id")

    # Test: No root directory.
    camera = copy.deepcopy(TEST_CAMERA)
    del camera[KEY_ROOT_DIRECTORY]
    client.async_get_cameras = AsyncMock(return_value={"cameras": [camera]})
    async_fire_time_changed(hass, dt_util.utcnow() + DEFAULT_SCAN_INTERVAL)
    await hass.async_block_till_done()

    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/four",
            "file_type": "8",
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(len(events)).to_equal(6)
    expect(events[-1].data).not_.to_contain("file_url")
    expect(events[-1].data).not_.to_contain("media_content_id")

    # Test: Device has incorrect device identifiers.
    device_registry.async_update_device(
        device_id=device.id, new_identifiers={("not", "motioneye")}
    )
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/five",
            "file_type": "8",
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(len(events)).to_equal(7)
    expect(events[-1].data).not_.to_contain("file_url")
    expect(events[-1].data).not_.to_contain("media_content_id")
