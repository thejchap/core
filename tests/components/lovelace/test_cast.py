"""Test the Lovelace Cast platform."""

from collections.abc import AsyncGenerator
from time import time
from unittest.mock import MagicMock, patch

from tryke import Depends, describe, expect, fixture, test

from homeassistant.components.lovelace import cast as lovelace_cast
from homeassistant.components.media_player import MediaClass
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component

from ._fixtures import mock_onboarding_done as mock_onboarding_done_fx

from tests.common import async_mock_service
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def root_object(
    hass: HomeAssistant = Depends(hass_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test getting a root object."""
    expect(
        await lovelace_cast.async_get_media_browser_root_object(hass, "some-type")
    ).to_equal([])

    root = await lovelace_cast.async_get_media_browser_root_object(
        hass, lovelace_cast.CAST_TYPE_CHROMECAST
    )
    expect(len(root)).to_be(1)
    item = root[0]
    expect(item.title).to_equal("Dashboards")
    expect(item.media_class).to_be(MediaClass.APP)
    expect(item.media_content_id).to_equal("")
    expect(item.media_content_type).to_equal(lovelace_cast.DOMAIN)
    expect(item.thumbnail).to_equal("/api/brands/integration/lovelace/logo.png")
    expect(item.can_play).to_be(False)
    expect(item.can_expand).to_be(True)


@test
async def browse_media_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test browse media checks valid URL."""
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    async with expect_raises_async(HomeAssistantError):
        await lovelace_cast.async_browse_media(
            hass, "lovelace", "", lovelace_cast.CAST_TYPE_CHROMECAST
        )

    expect(
        await lovelace_cast.async_browse_media(
            hass, "not_lovelace", "", lovelace_cast.CAST_TYPE_CHROMECAST
        )
    ).to_be(None)


with describe("with yaml dashboard"):

    @fixture
    async def mock_yaml_dashboard(
        hass: HomeAssistant = Depends(hass_fixture),
    ) -> AsyncGenerator[None]:
        """Mock the content of a YAML dashboard."""
        # Set up a YAML dashboard with 2 views.
        assert await async_setup_component(
            hass,
            "lovelace",
            {
                "lovelace": {
                    "dashboards": {
                        "yaml-with-views": {
                            "title": "YAML Title",
                            "mode": "yaml",
                            "filename": "bla.yaml",
                        }
                    }
                }
            },
        )

        with (
            patch(
                "homeassistant.components.lovelace.dashboard.load_yaml_dict",
                return_value={
                    "title": "YAML Title",
                    "views": [
                        {
                            "title": "Hello",
                        },
                        {"path": "second-view"},
                    ],
                },
            ),
            patch(
                "homeassistant.components.lovelace.dashboard.os.path.getmtime",
                return_value=time() + 10,
            ),
        ):
            yield

    with describe("with https url"):

        @fixture
        async def mock_https_url(
            hass: HomeAssistant = Depends(hass_fixture),
        ) -> None:
            """Mock valid URL."""
            await async_process_ha_core_config(
                hass,
                {"external_url": "https://example.com"},
            )

        @test
        async def browse_media(
            hass: HomeAssistant = Depends(hass_fixture),
            _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
        ) -> None:
            """Test browse media."""
            top_level_items = await lovelace_cast.async_browse_media(
                hass, "lovelace", "", lovelace_cast.CAST_TYPE_CHROMECAST
            )

            expect(len(top_level_items.children)).to_be(2)

            child_1 = top_level_items.children[0]
            expect(child_1.title).to_equal("Default")
            expect(child_1.media_class).to_be(MediaClass.APP)
            expect(child_1.media_content_id).to_equal(lovelace_cast.DEFAULT_DASHBOARD)
            expect(child_1.media_content_type).to_equal(lovelace_cast.DOMAIN)
            expect(child_1.thumbnail).to_equal(
                "/api/brands/integration/lovelace/logo.png"
            )
            expect(child_1.can_play).to_be(True)
            expect(child_1.can_expand).to_be(False)

            child_2 = top_level_items.children[1]
            expect(child_2.title).to_equal("YAML Title")
            expect(child_2.media_class).to_be(MediaClass.APP)
            expect(child_2.media_content_id).to_equal("yaml-with-views")
            expect(child_2.media_content_type).to_equal(lovelace_cast.DOMAIN)
            expect(child_2.thumbnail).to_equal(
                "/api/brands/integration/lovelace/logo.png"
            )
            expect(child_2.can_play).to_be(True)
            expect(child_2.can_expand).to_be(True)

            child_2 = await lovelace_cast.async_browse_media(
                hass,
                "lovelace",
                child_2.media_content_id,
                lovelace_cast.CAST_TYPE_CHROMECAST,
            )

            expect(len(child_2.children)).to_be(2)

            grandchild_1 = child_2.children[0]
            expect(grandchild_1.title).to_equal("Hello")
            expect(grandchild_1.media_class).to_be(MediaClass.APP)
            expect(grandchild_1.media_content_id).to_equal("yaml-with-views/0")
            expect(grandchild_1.media_content_type).to_equal(lovelace_cast.DOMAIN)
            expect(grandchild_1.thumbnail).to_equal(
                "/api/brands/integration/lovelace/logo.png"
            )
            expect(grandchild_1.can_play).to_be(True)
            expect(grandchild_1.can_expand).to_be(False)

            grandchild_2 = child_2.children[1]
            expect(grandchild_2.title).to_equal("second-view")
            expect(grandchild_2.media_class).to_be(MediaClass.APP)
            expect(grandchild_2.media_content_id).to_equal(
                "yaml-with-views/second-view"
            )
            expect(grandchild_2.media_content_type).to_equal(lovelace_cast.DOMAIN)
            expect(grandchild_2.thumbnail).to_equal(
                "/api/brands/integration/lovelace/logo.png"
            )
            expect(grandchild_2.can_play).to_be(True)
            expect(grandchild_2.can_expand).to_be(False)

            async with expect_raises_async(HomeAssistantError):
                await lovelace_cast.async_browse_media(
                    hass,
                    "lovelace",
                    "non-existing-dashboard",
                    lovelace_cast.CAST_TYPE_CHROMECAST,
                )

    @test
    async def play_media(
        hass: HomeAssistant = Depends(hass_fixture),
        _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
    ) -> None:
        """Test playing media."""
        calls = async_mock_service(hass, "cast", "show_lovelace_view")

        await lovelace_cast.async_play_media(
            hass,
            "media_player.my_cast",
            None,
            "lovelace",
            lovelace_cast.DEFAULT_DASHBOARD,
        )

        expect(len(calls)).to_be(1)
        expect(calls[0].data["entity_id"]).to_equal("media_player.my_cast")
        expect("dashboard_path" not in calls[0].data).to_be(True)
        expect(calls[0].data["view_path"]).to_equal("0")

        await lovelace_cast.async_play_media(
            hass,
            "media_player.my_cast",
            None,
            "lovelace",
            "yaml-with-views/second-view",
        )

        expect(len(calls)).to_be(2)
        expect(calls[1].data["entity_id"]).to_equal("media_player.my_cast")
        expect(calls[1].data["dashboard_path"]).to_equal("yaml-with-views")
        expect(calls[1].data["view_path"]).to_equal("second-view")
