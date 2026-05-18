"""Test add-on panel."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

from aiohasupervisor.models import IngressPanel
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import (
    hassio_env,
    homeassistant_info,
    ingress_panels,
    supervisor_is_connected,
)

from tests.common import MockUser
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
    hass_client as hass_client_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_all(
    _supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected),
    _homeassistant_info: AsyncMock = Depends(homeassistant_info),
    _ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Mock all setup requests."""


@test
async def hassio_addon_panel_startup(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Test startup and panel setup after event."""
    ingress_panels.return_value = {
        "test1": IngressPanel(enable=True, title="Test", icon="mdi:test", admin=False),
        "test2": IngressPanel(
            enable=False, title="Test 2", icon="mdi:test2", admin=True
        ),
    }

    with patch(
        "homeassistant.components.hassio.addon_panel._register_panel",
    ) as mock_panel:
        await async_setup_component(hass, "hassio", {})
        await hass.async_block_till_done()

        ingress_panels.assert_called_once()
        expect(mock_panel.called).to_equal(True)
        mock_panel.assert_called_with(
            hass,
            "test1",
            IngressPanel(enable=True, title="Test", icon="mdi:test", admin=False),
        )


@test
async def hassio_addon_panel_api(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Test panel api after event."""
    ingress_panels.return_value = {
        "test1": IngressPanel(enable=True, title="Test", icon="mdi:test", admin=False),
        "test2": IngressPanel(
            enable=False, title="Test 2", icon="mdi:test2", admin=True
        ),
    }

    with patch(
        "homeassistant.components.hassio.addon_panel._register_panel",
    ) as mock_panel:
        await async_setup_component(hass, "hassio", {})
        await hass.async_block_till_done()

        ingress_panels.assert_called_once()
        expect(mock_panel.called).to_equal(True)
        mock_panel.assert_called_with(
            hass,
            "test1",
            IngressPanel(enable=True, title="Test", icon="mdi:test", admin=False),
        )

        hass_client = await hass_client()

        resp = await hass_client.post("/api/hassio_push/panel/test2")
        expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)

        resp = await hass_client.post("/api/hassio_push/panel/test1")
        expect(resp.status).to_equal(HTTPStatus.OK)
        expect(mock_panel.call_count).to_equal(2)

        mock_panel.assert_called_with(
            hass,
            "test1",
            IngressPanel(enable=True, title="Test", icon="mdi:test", admin=False),
        )


@test
async def hassio_addon_panel_api_non_admin(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    ingress_panels: AsyncMock = Depends(ingress_panels),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test register panel api fails with non admin user."""
    ingress_panels.return_value = {
        "test1": IngressPanel(enable=True, title="Test", icon="mdi:test", admin=False),
    }

    with patch(
        "homeassistant.components.hassio.addon_panel._register_panel",
    ) as mock_panel:
        await async_setup_component(hass, "hassio", {})
        await hass.async_block_till_done()

        ingress_panels.assert_called_once()
        mock_panel.assert_called_once()

        mock_panel.reset_mock()
        hass_admin_user.groups = []
        hass_client = await hass_client()

        # Both should return unauthorized regardless of enabled as the endpoint requires
        # admin and the user is not admin
        resp = await hass_client.post("/api/hassio_push/panel/test2")
        expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)

        resp = await hass_client.post("/api/hassio_push/panel/test1")
        expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)

        mock_panel.assert_not_called()


@test
async def hassio_addon_panel_registration(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Test panel registration calls frontend.async_register_built_in_panel."""
    ingress_panels.return_value = {
        "test_addon": IngressPanel(
            enable=True, title="Test Addon", icon="mdi:test-tube", admin=True
        ),
    }

    with patch(
        "homeassistant.components.hassio.addon_panel.frontend.async_register_built_in_panel"
    ) as mock_register:
        await async_setup_component(hass, "hassio", {})
        await hass.async_block_till_done()

        # Verify that async_register_built_in_panel was called with correct arguments
        # for our test addon
        mock_register.assert_any_call(
            hass,
            "app",
            frontend_url_path="test_addon",
            sidebar_title="Test Addon",
            sidebar_icon="mdi:test-tube",
            require_admin=True,
            config={"addon": "test_addon"},
        )


@test
async def hassio_addon_panel_api_delete(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Test panel api delete."""
    ingress_panels.return_value = {
        "test1": IngressPanel(enable=True, title="Test", icon="mdi:test", admin=False),
    }
    await async_setup_component(hass, "hassio", {})
    await hass.async_block_till_done()

    hass_client = await hass_client()

    with patch(
        "homeassistant.components.hassio.addon_panel.frontend.async_remove_panel"
    ) as mock_remove:
        resp = await hass_client.delete("/api/hassio_push/panel/test1")
        expect(resp.status).to_equal(HTTPStatus.OK)
        mock_remove.assert_called_once_with(hass, "test1")


@test
async def hassio_addon_panel_api_delete_non_admin(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    ingress_panels: AsyncMock = Depends(ingress_panels),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test panel api delete fails with non admin user."""
    ingress_panels.return_value = {
        "test1": IngressPanel(enable=True, title="Test", icon="mdi:test", admin=False),
    }
    await async_setup_component(hass, "hassio", {})
    await hass.async_block_till_done()

    hass_admin_user.groups = []
    hass_client = await hass_client()

    with patch(
        "homeassistant.components.hassio.addon_panel.frontend.async_remove_panel"
    ) as mock_remove:
        resp = await hass_client.delete("/api/hassio_push/panel/test1")
        expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
        mock_remove.assert_not_called()
