"""The tests for Home Assistant frontend."""

from contextlib import nullcontext
from http import HTTPStatus
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp.test_utils import TestClient
from freezegun.api import FrozenDateTimeFactory
import re
import voluptuous as vol

from tryke import Depends, expect, fixture, test

from homeassistant.components.frontend import (
    CONF_DEVELOPMENT_PR,
    CONFIG_SCHEMA,
    CONF_GITHUB_TOKEN,
    CONF_THEMES,
    DEFAULT_THEME_COLOR,
    DOMAIN,
    EVENT_PANELS_UPDATED,
    THEMES_STORAGE_KEY,
    add_extra_js_url,
    async_panel_exists,
    async_register_built_in_panel,
    async_remove_panel,
    remove_extra_js_url,
)
from homeassistant.components.websocket_api import TYPE_RESULT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.loader import async_get_integration
from homeassistant.setup import async_setup_component

from tests.common import MockUser, async_capture_events, async_fire_time_changed
from tests.components.frontend._fixtures import (
    CONFIG_THEMES,
    MOCK_THEMES,
    frontend as frontend_fixture,
    frontend_themes as frontend_themes_fixture,
    ignore_frontend_deps as ignore_frontend_deps_fixture,
    mock_github_api as mock_github_api_fixture,
    mock_http_client as mock_http_client_fixture,
    mock_http_client_with_extra_js as mock_http_client_with_extra_js_fixture,
    mock_onboarded as mock_onboarded_fixture,
    themes_ws_client as themes_ws_client_fixture,
    ws_client as ws_client_fixture,
)
from tests.hass_fixtures import (
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    hass_client as hass_client_fixture,
    hass_storage as hass_storage_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import (
    ClientSessionGenerator,
    MockHAClientWebSocket,
    WebSocketGenerator,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@test
async def frontend_and_static(
    _trigger: int = Depends(_trigger_executor),
    _mock_onboarded: None = Depends(mock_onboarded_fixture),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
) -> None:
    """Test if we can get the frontend."""
    resp = await mock_http_client.get("")
    expect(resp.status).to_equal(200)
    expect("cache-control" not in resp.headers).to_be(True)

    text = await resp.text()

    # Test we can retrieve frontend.js
    frontendjs = re.search(r"(?P<app>\/frontend_es5\/app.[A-Za-z0-9_-]{16}.js)", text)

    expect(frontendjs is not None).to_be(True)
    resp = await mock_http_client.get(frontendjs.groups(0)[0])
    expect(resp.status).to_equal(200)
    expect("public" in resp.headers.get("cache-control")).to_be(True)


@test.cases(
    test.case("modern", sw_url="/sw-modern.js"),
    test.case("legacy", sw_url="/sw-legacy.js"),
)
async def dont_cache_service_worker(
    sw_url: str,
    _trigger: int = Depends(_trigger_executor),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
) -> None:
    """Test that we don't cache the service worker."""
    resp = await mock_http_client.get(sw_url)
    expect(resp.status).to_equal(200)
    expect("cache-control" not in resp.headers).to_be(True)


@test
async def http_404(
    _trigger: int = Depends(_trigger_executor),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
) -> None:
    """Test for HTTP 404 error."""
    resp = await mock_http_client.get("/not-existing")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)


@test
async def we_cannot_post_to_root(
    _trigger: int = Depends(_trigger_executor),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
) -> None:
    """Test that POST is not allow to root."""
    resp = await mock_http_client.post("/")
    expect(resp.status).to_equal(405)


@test
async def themes_api(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    themes_ws_client: MockHAClientWebSocket = Depends(themes_ws_client_fixture),
) -> None:
    """Test that /api/themes returns correct data."""
    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("default")
    expect(msg["result"]["default_dark_theme"]).to_be(None)
    expect(msg["result"]["themes"]).to_equal(MOCK_THEMES)

    # recovery mode
    hass.config.recovery_mode = True
    await themes_ws_client.send_json({"id": 6, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("default")
    expect(msg["result"]["themes"]).to_equal({})

    # safe mode
    hass.config.recovery_mode = False
    hass.config.safe_mode = True
    await themes_ws_client.send_json({"id": 7, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("default")
    expect(msg["result"]["themes"]).to_equal({})


@test
async def themes_persist(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _ignore: None = Depends(ignore_frontend_deps_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test that theme settings are restores after restart."""
    hass_storage[THEMES_STORAGE_KEY] = {
        "key": THEMES_STORAGE_KEY,
        "version": 1,
        "data": {
            "frontend_default_theme": "happy",
            "frontend_default_dark_theme": "dark",
        },
    }

    expect(await async_setup_component(hass, "frontend", CONFIG_THEMES)).to_be(True)
    themes_ws_client = await hass_ws_client(hass)

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("happy")
    expect(msg["result"]["default_dark_theme"]).to_equal("dark")


@test
async def themes_save_storage(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _frontend: None = Depends(frontend_themes_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test that theme settings are restores after restart."""
    await hass.services.async_call(DOMAIN, "set_theme", {"name": "happy"}, blocking=True)

    await hass.services.async_call(
        DOMAIN, "set_theme", {"name": "dark", "mode": "dark"}, blocking=True
    )

    # To trigger the call_later
    freezer.tick(60.0)
    async_fire_time_changed(hass)
    # To execute the save
    await hass.async_block_till_done()

    expect(hass_storage[THEMES_STORAGE_KEY]["data"]).to_equal(
        {
            "frontend_default_theme": "happy",
            "frontend_default_dark_theme": "dark",
        }
    )


@test
async def themes_save_storage_new_schema(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _frontend: None = Depends(frontend_themes_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test that theme settings are restores after restart."""
    await hass.services.async_call(
        DOMAIN, "set_theme", {"name": "happy", "name_dark": "dark"}, blocking=True
    )

    # To trigger the call_later
    freezer.tick(60.0)
    async_fire_time_changed(hass)
    # To execute the save
    await hass.async_block_till_done()

    expect(hass_storage[THEMES_STORAGE_KEY]["data"]).to_equal(
        {
            "frontend_default_theme": "happy",
            "frontend_default_dark_theme": "dark",
        }
    )


@test
async def themes_set_theme(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    themes_ws_client: MockHAClientWebSocket = Depends(themes_ws_client_fixture),
) -> None:
    """Test frontend.set_theme service."""
    await hass.services.async_call(DOMAIN, "set_theme", {"name": "happy"}, blocking=True)

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("happy")

    await hass.services.async_call(
        DOMAIN, "set_theme", {"name": "default"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 6, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("default")

    await hass.services.async_call(DOMAIN, "set_theme", {"name": "happy"}, blocking=True)

    await hass.services.async_call(DOMAIN, "set_theme", {"name": "none"}, blocking=True)

    await themes_ws_client.send_json({"id": 7, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("default")


@test
async def themes_set_theme_wrong_name(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    themes_ws_client: MockHAClientWebSocket = Depends(themes_ws_client_fixture),
) -> None:
    """Test frontend.set_theme service called with wrong name."""
    async with expect_raises_async(
        vol.error.MultipleInvalid, match="Theme wrong not found"
    ):
        await hass.services.async_call(
            DOMAIN, "set_theme", {"name": "wrong"}, blocking=True
        )

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})

    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("default")


@test
async def themes_set_dark_theme(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    themes_ws_client: MockHAClientWebSocket = Depends(themes_ws_client_fixture),
) -> None:
    """Test frontend.set_theme service called with dark mode."""
    await hass.services.async_call(
        DOMAIN, "set_theme", {"name": "dark", "mode": "dark"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_dark_theme"]).to_equal("dark")

    await hass.services.async_call(
        DOMAIN, "set_theme", {"name": "default", "mode": "dark"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 6, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_dark_theme"]).to_equal("default")

    await hass.services.async_call(
        DOMAIN, "set_theme", {"name": "none", "mode": "dark"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 7, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_dark_theme"]).to_be(None)

    await hass.services.async_call(
        DOMAIN, "set_theme", {"name": "light_and_dark", "mode": "dark"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 8, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_dark_theme"]).to_equal("light_and_dark")


@test
async def themes_set_combined_theme(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    themes_ws_client: MockHAClientWebSocket = Depends(themes_ws_client_fixture),
) -> None:
    """Test frontend.set_theme service setting both light and dark modes."""
    await hass.services.async_call(
        DOMAIN, "set_theme", {"name_dark": "dark"}, blocking=True
    )

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("default")
    expect(msg["result"]["default_dark_theme"]).to_equal("dark")

    await hass.services.async_call(DOMAIN, "set_theme", {"name": "happy"}, blocking=True)

    await themes_ws_client.send_json({"id": 6, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("happy")
    expect(msg["result"]["default_dark_theme"]).to_equal("dark")

    await hass.services.async_call(
        DOMAIN,
        "set_theme",
        {"name": "light_only", "name_dark": "dark_only"},
        blocking=True,
    )

    await themes_ws_client.send_json({"id": 7, "type": "frontend/get_themes"})
    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_theme"]).to_equal("light_only")
    expect(msg["result"]["default_dark_theme"]).to_equal("dark_only")


@test.cases(
    test.case("wrong_name_dark_mode", schema={"name": "wrong", "mode": "dark"}),
    test.case("wrong_name_dark", schema={"name_dark": "wrong"}),
)
async def themes_set_dark_theme_wrong_name(
    schema: dict[str, str],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _frontend: None = Depends(frontend_fixture),
    themes_ws_client: MockHAClientWebSocket = Depends(themes_ws_client_fixture),
) -> None:
    """Test frontend.set_theme service called with mode dark and wrong name."""
    async with expect_raises_async(
        vol.error.MultipleInvalid, match="Theme wrong not found"
    ):
        await hass.services.async_call(DOMAIN, "set_theme", schema, blocking=True)

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})

    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["default_dark_theme"]).to_be(None)


@test
async def themes_reload_themes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _frontend: None = Depends(frontend_fixture),
    themes_ws_client: MockHAClientWebSocket = Depends(themes_ws_client_fixture),
) -> None:
    """Test frontend.reload_themes service."""
    with patch(
        "homeassistant.components.frontend.async_hass_config_yaml",
        return_value={DOMAIN: {CONF_THEMES: {"sad": {"primary-color": "blue"}}}},
    ):
        async with expect_raises_async(
            vol.error.MultipleInvalid, match="Theme happy not found"
        ):
            await hass.services.async_call(
                DOMAIN, "set_theme", {"name": "happy"}, blocking=True
            )
        await hass.services.async_call(DOMAIN, "reload_themes", blocking=True)

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})

    msg = await themes_ws_client.receive_json()

    expect(msg["result"]["themes"]).to_equal({"sad": {"primary-color": "blue"}})
    expect(msg["result"]["default_theme"]).to_equal("default")


@test.cases(
    test.case(
        "invalid0",
        invalid_theme={"invalid0": "blue"},
        error="expected a dictionary",
        log=None,
    ),
    test.case(
        "invalid1",
        invalid_theme={
            "invalid1": {
                "primary-color": "black",
                "modes": "light:{} dark:{}",
            }
        },
        error=None,
        log="expected a dictionary",
    ),
    test.case(
        "invalid2",
        invalid_theme={"invalid2": None},
        error="expected a dictionary",
        log=None,
    ),
    test.case(
        "invalid3",
        invalid_theme={
            "invalid3": {
                "primary-color": "black",
                "modes": {},
            }
        },
        error=None,
        log="must contain at least one of light, dark",
    ),
    test.case(
        "invalid4",
        invalid_theme={
            "invalid4": {
                "primary-color": "black",
                "modes": None,
            }
        },
        error="string value is None for dictionary value",
        log=None,
    ),
    test.case(
        "invalid5",
        invalid_theme={
            "invalid5": {
                "primary-color": "black",
                "modes": {"light": {}, "dank": {}},
            }
        },
        error="extra keys not allowed.*dank",
        log=None,
    ),
)
async def themes_reload_invalid(
    invalid_theme: dict,
    error: str | None,
    log: str | None,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _frontend: None = Depends(frontend_fixture),
    themes_ws_client: MockHAClientWebSocket = Depends(themes_ws_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test frontend.reload_themes service with an invalid theme."""
    with patch(
        "homeassistant.components.frontend.async_hass_config_yaml",
        return_value={DOMAIN: {CONF_THEMES: {"happy": {"primary-color": "pink"}}}},
    ):
        await hass.services.async_call(DOMAIN, "reload_themes", blocking=True)

    with patch(
        "homeassistant.components.frontend.async_hass_config_yaml",
        return_value={DOMAIN: {CONF_THEMES: invalid_theme}},
    ):
        if error is not None:
            async with expect_raises_async(
                HomeAssistantError, match=rf"Failed to reload themes.*{error}"
            ):
                await hass.services.async_call(
                    DOMAIN, "reload_themes", blocking=True
                )
        else:
            with nullcontext():
                await hass.services.async_call(
                    DOMAIN, "reload_themes", blocking=True
                )

    if log is not None:
        expect(log in caplog.text).to_be(True)

    await themes_ws_client.send_json({"id": 5, "type": "frontend/get_themes"})

    msg = await themes_ws_client.receive_json()

    expected_themes = {"happy": {"primary-color": "pink"}}
    if error is None:
        expected_themes = {}

    expect(msg["result"]["themes"]).to_equal(expected_themes)
    expect(msg["result"]["default_theme"]).to_equal("default")


@test
async def missing_themes(
    _trigger: int = Depends(_trigger_executor),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test that themes API works when themes are not defined."""
    await ws_client.send_json({"id": 5, "type": "frontend/get_themes"})

    msg = await ws_client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(msg["result"]["default_theme"]).to_equal("default")
    expect(msg["result"]["themes"]).to_equal({})


@test
async def extra_js(
    _trigger: int = Depends(_trigger_executor),
    _mock_onboarded: None = Depends(mock_onboarded_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    mock_http_client_with_extra_js: TestClient = Depends(
        mock_http_client_with_extra_js_fixture
    ),
) -> None:
    """Test that extra javascript is loaded."""

    async def get_response():
        resp = await mock_http_client_with_extra_js.get("")
        expect(resp.status).to_equal(200)
        expect("cache-control" not in resp.headers).to_be(True)

        return await resp.text()

    text = await get_response()
    expect('"/local/my_module.js"' in text).to_be(True)
    expect('"/local/my_es5.js"' in text).to_be(True)

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "frontend/subscribe_extra_js"})
    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    subscription_id = msg["id"]

    # Test dynamically adding and removing extra javascript
    add_extra_js_url(hass, "/local/my_module_2.js", False)
    add_extra_js_url(hass, "/local/my_es5_2.js", True)
    text = await get_response()
    expect('"/local/my_module_2.js"' in text).to_be(True)
    expect('"/local/my_es5_2.js"' in text).to_be(True)

    msg = await client.receive_json()
    expect(msg["id"]).to_equal(subscription_id)
    expect(msg["event"]).to_equal(
        {
            "change_type": "added",
            "item": {"type": "module", "url": "/local/my_module_2.js"},
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(subscription_id)
    expect(msg["event"]).to_equal(
        {
            "change_type": "added",
            "item": {"type": "es5", "url": "/local/my_es5_2.js"},
        }
    )

    remove_extra_js_url(hass, "/local/my_module_2.js", False)
    remove_extra_js_url(hass, "/local/my_es5_2.js", True)
    text = await get_response()
    expect('"/local/my_module_2.js"' not in text).to_be(True)
    expect('"/local/my_es5_2.js"' not in text).to_be(True)

    msg = await client.receive_json()
    expect(msg["id"]).to_equal(subscription_id)
    expect(msg["event"]).to_equal(
        {
            "change_type": "removed",
            "item": {"type": "module", "url": "/local/my_module_2.js"},
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(subscription_id)
    expect(msg["event"]).to_equal(
        {
            "change_type": "removed",
            "item": {"type": "es5", "url": "/local/my_es5_2.js"},
        }
    )

    # Remove again should not raise
    remove_extra_js_url(hass, "/local/my_module_2.js", False)
    remove_extra_js_url(hass, "/local/my_es5_2.js", True)
    text = await get_response()
    expect('"/local/my_module_2.js"' not in text).to_be(True)
    expect('"/local/my_es5_2.js"' not in text).to_be(True)

    # safe mode
    hass.config.safe_mode = True
    text = await get_response()
    expect('"/local/my_module.js"' not in text).to_be(True)
    expect('"/local/my_es5.js"' not in text).to_be(True)

    # Test dynamically adding extra javascript
    add_extra_js_url(hass, "/local/my_module_2.js", False)
    add_extra_js_url(hass, "/local/my_es5_2.js", True)
    text = await get_response()
    expect('"/local/my_module_2.js"' not in text).to_be(True)
    expect('"/local/my_es5_2.js"' not in text).to_be(True)


@test
async def get_panels(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test get_panels command."""
    events = async_capture_events(hass, EVENT_PANELS_UPDATED)

    resp = await mock_http_client.get("/map")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)

    async_register_built_in_panel(
        hass, "map", "Map", "mdi:tooltip-account", require_admin=True
    )

    resp = await mock_http_client.get("/map")
    expect(resp.status).to_equal(200)

    expect(len(events)).to_equal(1)

    client = await hass_ws_client(hass)
    await client.send_json({"id": 5, "type": "get_panels"})

    msg = await client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(msg["result"]["map"]["component_name"]).to_equal("map")
    expect(msg["result"]["map"]["url_path"]).to_equal("map")
    expect(msg["result"]["map"]["icon"]).to_equal("mdi:tooltip-account")
    expect(msg["result"]["map"]["title"]).to_equal("Map")
    expect(msg["result"]["map"]["require_admin"]).to_be(True)
    expect(msg["result"]["map"]["default_visible"]).to_be(True)

    async_remove_panel(hass, "map")

    resp = await mock_http_client.get("/map")
    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)

    expect(len(events)).to_equal(2)

    # Remove again, will warn but not trigger event
    async_remove_panel(hass, "map")
    expect("Removing unknown panel map" in caplog.text).to_be(True)
    caplog.clear()

    # Remove again, without warning
    async_remove_panel(hass, "map", warn_if_unknown=False)
    expect("Removing unknown panel map" not in caplog.text).to_be(True)


@test
async def panel_exists(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _frontend: None = Depends(frontend_fixture),
) -> None:
    """Test async_panel_exists helper."""
    expect(async_panel_exists(hass, "test_panel")).to_be(False)

    async_register_built_in_panel(hass, "test_panel")
    expect(async_panel_exists(hass, "test_panel")).to_be(True)

    async_remove_panel(hass, "test_panel")
    expect(async_panel_exists(hass, "test_panel")).to_be(False)


@test
async def get_panels_non_admin(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test get_panels command."""
    hass_admin_user.groups = []

    async_register_built_in_panel(
        hass, "map", "Map", "mdi:tooltip-account", require_admin=True
    )
    async_register_built_in_panel(hass, "history", "History", "mdi:history")

    await ws_client.send_json({"id": 5, "type": "get_panels"})

    msg = await ws_client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect("history" in msg["result"]).to_be(True)
    expect("map" not in msg["result"]).to_be(True)


@test
async def panel_sidebar_default_visible(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
) -> None:
    """Test sidebar_default_visible property in panels."""
    async_register_built_in_panel(hass, "default_panel", "Default Panel")
    async_register_built_in_panel(
        hass,
        "visible_panel",
        "Visible Panel",
        "mdi:eye",
        sidebar_default_visible=True,
    )
    async_register_built_in_panel(
        hass,
        "hidden_panel",
        "Hidden Panel",
        "mdi:eye-off",
        sidebar_default_visible=False,
    )

    client = await hass_ws_client(hass)
    await client.send_json({"id": 5, "type": "get_panels"})

    msg = await client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(msg["result"]["default_panel"]["default_visible"]).to_be(True)
    expect(msg["result"]["visible_panel"]["default_visible"]).to_be(True)
    expect(msg["result"]["hidden_panel"]["default_visible"]).to_be(False)


@test
async def get_translations(
    _trigger: int = Depends(_trigger_executor),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test get_translations command."""
    with patch(
        "homeassistant.components.frontend.async_get_translations",
        side_effect=lambda hass, lang, category, integrations, config_flow: {
            "lang": lang
        },
    ):
        await ws_client.send_json(
            {
                "id": 5,
                "type": "frontend/get_translations",
                "language": "nl",
                "category": "lang",
            }
        )
        msg = await ws_client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"resources": {"lang": "nl"}})


@test
async def get_translations_for_integrations(
    _trigger: int = Depends(_trigger_executor),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test get_translations for integrations command."""
    with patch(
        "homeassistant.components.frontend.async_get_translations",
        side_effect=lambda hass, lang, category, integration, config_flow: {
            "lang": lang,
            "integration": integration,
        },
    ):
        await ws_client.send_json(
            {
                "id": 5,
                "type": "frontend/get_translations",
                "integration": ["frontend", "http"],
                "language": "nl",
                "category": "lang",
            }
        )
        msg = await ws_client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(set(msg["result"]["resources"]["integration"])).to_equal(
        {"frontend", "http"}
    )


@test
async def get_translations_for_single_integration(
    _trigger: int = Depends(_trigger_executor),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test get_translations for integration command."""
    with patch(
        "homeassistant.components.frontend.async_get_translations",
        side_effect=lambda hass, lang, category, integrations, config_flow: {
            "lang": lang,
            "integration": integrations,
        },
    ):
        await ws_client.send_json(
            {
                "id": 5,
                "type": "frontend/get_translations",
                "integration": "http",
                "language": "nl",
                "category": "lang",
            }
        )
        msg = await ws_client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {"resources": {"lang": "nl", "integration": ["http"]}}
    )


@test
async def auth_load(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test auth component loaded by default."""
    frontend = await async_get_integration(hass, "frontend")
    expect("auth" in frontend.dependencies).to_be(True)


@test
async def onboarding_load(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test onboarding component loaded by default."""
    frontend = await async_get_integration(hass, "frontend")
    expect("onboarding" in frontend.dependencies).to_be(True)


@test
async def auth_authorize(
    _trigger: int = Depends(_trigger_executor),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
) -> None:
    """Test the authorize endpoint works."""
    resp = await mock_http_client.get(
        "/auth/authorize?response_type=code&client_id=https://localhost/&"
        "redirect_uri=https://localhost/&state=123%23456"
    )
    expect(resp.status).to_equal(200)
    # No caching of auth page.
    expect("cache-control" not in resp.headers).to_be(True)

    text = await resp.text()

    # Test we can retrieve authorize.js
    authorizejs = re.search(
        r"(?P<app>\/frontend_latest\/authorize.[A-Za-z0-9_-]{16}.js)", text
    )

    expect(authorizejs is not None).to_be(True)
    resp = await mock_http_client.get(authorizejs.groups(0)[0])
    expect(resp.status).to_equal(200)
    expect("public" in resp.headers.get("cache-control")).to_be(True)


@test
async def get_version(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test get_version command."""
    frontend = await async_get_integration(hass, "frontend")
    cur_version = next(
        req.split("==", 1)[1]
        for req in frontend.requirements
        if req.startswith("home-assistant-frontend==")
    )

    await ws_client.send_json({"id": 5, "type": "frontend/get_version"})
    msg = await ws_client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"version": cur_version})


@test.cases(
    test.case(
        "change_password",
        from_url="/.well-known/change-password",
        to_url="/profile",
        expected_status=302,
    ),
    test.case(
        "developer_tools",
        from_url="/developer-tools",
        to_url="/config/developer-tools",
        expected_status=301,
    ),
    test.case(
        "developer_tools_yaml",
        from_url="/developer-tools/yaml",
        to_url="/config/developer-tools/yaml",
        expected_status=301,
    ),
    test.case(
        "developer_tools_state",
        from_url="/developer-tools/state",
        to_url="/config/developer-tools/state",
        expected_status=301,
    ),
    test.case(
        "developer_tools_action",
        from_url="/developer-tools/action",
        to_url="/config/developer-tools/action",
        expected_status=301,
    ),
    test.case(
        "developer_tools_template",
        from_url="/developer-tools/template",
        to_url="/config/developer-tools/template",
        expected_status=301,
    ),
    test.case(
        "developer_tools_event",
        from_url="/developer-tools/event",
        to_url="/config/developer-tools/event",
        expected_status=301,
    ),
    test.case(
        "developer_tools_debug",
        from_url="/developer-tools/debug",
        to_url="/config/developer-tools/debug",
        expected_status=301,
    ),
    test.case(
        "shopping_list",
        from_url="/shopping-list",
        to_url="/todo",
        expected_status=301,
    ),
)
async def static_paths(
    from_url: str,
    to_url: str,
    expected_status: int,
    _trigger: int = Depends(_trigger_executor),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
) -> None:
    """Test static paths."""
    resp = await mock_http_client.get(from_url, allow_redirects=False)
    expect(resp.status).to_equal(expected_status)
    expect(resp.headers["location"]).to_equal(to_url)


@test
async def manifest_json(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _frontend: None = Depends(frontend_themes_fixture),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
) -> None:
    """Test for fetching manifest.json."""
    resp = await mock_http_client.get("/manifest.json")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect("cache-control" not in resp.headers).to_be(True)

    json = await resp.json()
    expect(json["theme_color"]).to_equal(DEFAULT_THEME_COLOR)

    await hass.services.async_call(DOMAIN, "set_theme", {"name": "happy"}, blocking=True)
    await hass.async_block_till_done()

    resp = await mock_http_client.get("/manifest.json")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect("cache-control" not in resp.headers).to_be(True)

    json = await resp.json()
    expect(json["theme_color"] != DEFAULT_THEME_COLOR).to_be(True)


@test
async def static_path_cache(
    _trigger: int = Depends(_trigger_executor),
    mock_http_client: TestClient = Depends(mock_http_client_fixture),
) -> None:
    """Test static paths cache."""
    resp = await mock_http_client.get("/lovelace/default_view", allow_redirects=False)
    expect(resp.status).to_equal(404)

    resp = await mock_http_client.get("/frontend_latest/", allow_redirects=False)
    expect(resp.status).to_equal(403)

    resp = await mock_http_client.get("/static/icons/favicon.ico", allow_redirects=False)
    expect(resp.status).to_equal(200)

    # and again to make sure the cache works
    resp = await mock_http_client.get("/static/icons/favicon.ico", allow_redirects=False)
    expect(resp.status).to_equal(200)

    resp = await mock_http_client.get(
        "/static/fonts/roboto/Roboto-Bold.woff2", allow_redirects=False
    )
    expect(resp.status).to_equal(200)

    resp = await mock_http_client.get("/static/does-not-exist", allow_redirects=False)
    expect(resp.status).to_equal(404)

    # and again to make sure the cache works
    resp = await mock_http_client.get("/static/does-not-exist", allow_redirects=False)
    expect(resp.status).to_equal(404)


@test
async def get_icons(
    _trigger: int = Depends(_trigger_executor),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test get_icons command."""
    with patch(
        "homeassistant.components.frontend.async_get_icons",
        side_effect=lambda hass, category, integrations: {},
    ):
        await ws_client.send_json(
            {
                "id": 5,
                "type": "frontend/get_icons",
                "category": "entity_component",
            }
        )
        msg = await ws_client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"resources": {}})


@test
async def get_icons_for_integrations(
    _trigger: int = Depends(_trigger_executor),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test get_icons for integrations command."""
    with patch(
        "homeassistant.components.frontend.async_get_icons",
        side_effect=lambda hass, category, integrations: {
            integration: {} for integration in integrations
        },
    ):
        await ws_client.send_json(
            {
                "id": 5,
                "type": "frontend/get_icons",
                "integration": ["frontend", "http"],
                "category": "entity",
            }
        )
        msg = await ws_client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(set(msg["result"]["resources"])).to_equal({"frontend", "http"})


@test
async def get_icons_for_single_integration(
    _trigger: int = Depends(_trigger_executor),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test get_icons for integration command."""
    with patch(
        "homeassistant.components.frontend.async_get_icons",
        side_effect=lambda hass, category, integrations: {
            integration: {} for integration in integrations
        },
    ):
        await ws_client.send_json(
            {
                "id": 5,
                "type": "frontend/get_icons",
                "integration": "http",
                "category": "entity",
            }
        )
        msg = await ws_client.receive_json()

    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"resources": {"http": {}}})


@test
async def www_local_dir(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test local www folder."""
    hass.config.config_dir = str(tmp_path)
    tmp_path_www = tmp_path / "www"
    x_txt_file = tmp_path_www / "x.txt"

    def _create_www_and_x_txt():
        tmp_path_www.mkdir()
        x_txt_file.write_text("any")

    await hass.async_add_executor_job(_create_www_and_x_txt)

    expect(await async_setup_component(hass, "frontend", {})).to_be(True)
    client = await hass_client()
    resp = await client.get("/local/x.txt")
    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def development_pr_and_github_token_inclusive(
    _trigger: int = Depends(_trigger_executor),
) -> None:
    """Test that development_pr and github_token must both be set or neither."""
    # Both present - valid
    valid_config = {
        DOMAIN: {
            CONF_DEVELOPMENT_PR: 12345,
            CONF_GITHUB_TOKEN: "test_token",
        }
    }
    expect(bool(CONFIG_SCHEMA(valid_config))).to_be(True)

    valid_config_empty: dict[str, dict[str, Any]] = {DOMAIN: {}}
    expect(bool(CONFIG_SCHEMA(valid_config_empty))).to_be(True)

    invalid_config_pr_only = {
        DOMAIN: {
            CONF_DEVELOPMENT_PR: 12345,
        }
    }
    async with expect_raises_async(vol.Invalid, match="some but not all"):
        CONFIG_SCHEMA(invalid_config_pr_only)

    invalid_config_token_only: dict[str, dict[str, Any]] = {
        DOMAIN: {CONF_GITHUB_TOKEN: "test_token"}
    }
    async with expect_raises_async(vol.Invalid, match="some but not all"):
        CONFIG_SCHEMA(invalid_config_token_only)


@test
async def setup_with_development_pr_and_token(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that setup succeeds when both development_pr and github_token are provided."""
    hass.config.config_dir = str(tmp_path)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        content=b"fake zip data",
    )

    config = {
        DOMAIN: {
            CONF_DEVELOPMENT_PR: 12345,
            CONF_GITHUB_TOKEN: "test_token",
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    # Verify GitHub API was called
    expect(mock_github_api.generic.call_count >= 2).to_be(True)


@test
async def setup_cleans_up_pr_cache_when_not_configured(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test that PR cache is cleaned up when no PR is configured."""
    hass.config.config_dir = str(tmp_path)

    pr_cache_dir = tmp_path / ".cache" / "frontend" / "development_artifacts"
    pr_cache_dir.mkdir(parents=True)
    (pr_cache_dir / "test_file.txt").write_text("test")

    config: dict[str, dict[str, Any]] = {DOMAIN: {}}

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    expect(pr_cache_dir.exists()).to_be(False)


@test
async def setup_with_development_pr_unexpected_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that setup handles unexpected errors during PR download gracefully."""
    hass.config.config_dir = str(tmp_path)

    with patch(
        "homeassistant.components.frontend.download_pr_artifact",
        side_effect=RuntimeError("Unexpected error"),
    ):
        config = {
            DOMAIN: {
                CONF_DEVELOPMENT_PR: 12345,
                CONF_GITHUB_TOKEN: "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect("Unexpected error downloading PR #12345" in caplog.text).to_be(True)


@test
async def update_panel(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test frontend/update_panel command."""
    # Verify initial state
    await ws_client.send_json({"id": 1, "type": "get_panels"})
    msg = await ws_client.receive_json()
    expect(msg["result"]["light"]["icon"]).to_equal("mdi:lamps")
    expect(msg["result"]["light"]["title"]).to_equal("light")
    expect(msg["result"]["light"]["require_admin"]).to_be(False)

    # Update the light panel
    events = async_capture_events(hass, EVENT_PANELS_UPDATED)
    await ws_client.send_json(
        {
            "id": 2,
            "type": "frontend/update_panel",
            "url_path": "light",
            "title": "My Lights",
            "icon": "mdi:lightbulb",
            "require_admin": True,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(len(events)).to_equal(1)

    # Verify the panel was updated
    await ws_client.send_json({"id": 3, "type": "get_panels"})
    msg = await ws_client.receive_json()
    expect(msg["result"]["light"]["icon"]).to_equal("mdi:lightbulb")
    expect(msg["result"]["light"]["title"]).to_equal("My Lights")
    expect(msg["result"]["light"]["require_admin"]).to_be(True)


@test
async def update_panel_partial(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test that partial updates only change specified properties."""
    # Update only title
    await ws_client.send_json(
        {
            "id": 1,
            "type": "frontend/update_panel",
            "url_path": "climate",
            "title": "HVAC",
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)

    # Verify only title changed, others kept defaults
    await ws_client.send_json({"id": 2, "type": "get_panels"})
    msg = await ws_client.receive_json()
    expect(msg["result"]["climate"]["title"]).to_equal("HVAC")
    expect(msg["result"]["climate"]["icon"]).to_equal("mdi:home-thermometer")
    expect(msg["result"]["climate"]["require_admin"]).to_be(False)
    expect(msg["result"]["climate"]["default_visible"]).to_be(True)


@test
async def update_panel_not_found(
    _trigger: int = Depends(_trigger_executor),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test that non-existent panels are rejected."""
    await ws_client.send_json(
        {
            "id": 1,
            "type": "frontend/update_panel",
            "url_path": "nonexistent",
            "title": "Does Not Exist",
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("not_found")


@test
async def update_panel_requires_admin(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test that non-admin users cannot update panels."""
    hass_admin_user.groups = []

    await ws_client.send_json(
        {
            "id": 1,
            "type": "frontend/update_panel",
            "url_path": "light",
            "title": "My Lights",
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(False)


@test
async def update_panel_persists(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _ignore: None = Depends(ignore_frontend_deps_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test that panel config is loaded from storage on startup."""
    hass_storage["frontend_panels"] = {
        "key": "frontend_panels",
        "version": 1,
        "data": {
            "light": {
                "title": "Saved Lights",
                "icon": "mdi:lamp",
                "require_admin": True,
            },
        },
    }

    expect(await async_setup_component(hass, "frontend", {})).to_be(True)
    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "get_panels"})
    msg = await client.receive_json()
    expect(msg["result"]["light"]["title"]).to_equal("Saved Lights")
    expect(msg["result"]["light"]["icon"]).to_equal("mdi:lamp")
    expect(msg["result"]["light"]["require_admin"]).to_be(True)

    # Verify other panels still have defaults
    expect(msg["result"]["climate"]["title"]).to_equal("climate")
    expect(msg["result"]["climate"]["icon"]).to_equal("mdi:home-thermometer")


@test
async def update_panel_reset_param(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test that setting a param to None resets it to the original value."""
    # First set a custom icon
    await ws_client.send_json(
        {
            "id": 1,
            "type": "frontend/update_panel",
            "url_path": "security",
            "icon": "mdi:shield",
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)

    await ws_client.send_json({"id": 2, "type": "get_panels"})
    msg = await ws_client.receive_json()
    expect(msg["result"]["security"]["icon"]).to_equal("mdi:shield")

    # Reset icon by setting to None - should restore original
    await ws_client.send_json(
        {
            "id": 3,
            "type": "frontend/update_panel",
            "url_path": "security",
            "icon": None,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)

    await ws_client.send_json({"id": 4, "type": "get_panels"})
    msg = await ws_client.receive_json()
    expect(msg["result"]["security"]["icon"]).to_equal("mdi:security")


@test
async def update_panel_toggle_show_in_sidebar(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ws_client: MockHAClientWebSocket = Depends(ws_client_fixture),
) -> None:
    """Test that show_in_sidebar is returned without altering title and icon."""
    # Verify initial state has title and icon
    await ws_client.send_json({"id": 1, "type": "get_panels"})
    msg = await ws_client.receive_json()
    expect(msg["result"]["light"]["title"]).to_equal("light")
    expect(msg["result"]["light"]["icon"]).to_equal("mdi:lamps")
    expect(msg["result"]["light"]["show_in_sidebar"]).to_be(False)

    # Show in sidebar
    await ws_client.send_json(
        {
            "id": 2,
            "type": "frontend/update_panel",
            "url_path": "light",
            "show_in_sidebar": True,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)

    # Title and icon should remain unchanged and show_in_sidebar should be True
    await ws_client.send_json({"id": 3, "type": "get_panels"})
    msg = await ws_client.receive_json()
    expect(msg["result"]["light"]["title"]).to_equal("light")
    expect(msg["result"]["light"]["icon"]).to_equal("mdi:lamps")
    expect(msg["result"]["light"]["show_in_sidebar"]).to_be(True)

    # Reset show_in_sidebar to panel default
    await ws_client.send_json(
        {
            "id": 4,
            "type": "frontend/update_panel",
            "url_path": "light",
            "show_in_sidebar": None,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)

    # show_in_sidebar should be restored to built-in default
    await ws_client.send_json({"id": 5, "type": "get_panels"})
    msg = await ws_client.receive_json()
    expect(msg["result"]["light"]["title"]).to_equal("light")
    expect(msg["result"]["light"]["icon"]).to_equal("mdi:lamps")
    expect(msg["result"]["light"]["show_in_sidebar"]).to_be(False)


@test
async def panels_config_invalid_storage(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that corrupted panel storage is ignored with a warning."""
    hass_storage["frontend_panels"] = {
        "key": "frontend_panels",
        "version": 1,
        "data": "not_a_dict",
    }

    expect(await async_setup_component(hass, "frontend", {})).to_be(True)
    expect("Ignoring invalid panel storage data" in caplog.text).to_be(True)

    client = await hass_ws_client(hass)

    # Panels should still load with defaults
    await client.send_json({"id": 1, "type": "get_panels"})
    msg = await client.receive_json()
    expect(msg["result"]["light"]["title"]).to_equal("light")
    expect(msg["result"]["light"]["icon"]).to_equal("mdi:lamps")
