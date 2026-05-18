"""The tests for the Yamaha Media player platform."""

from unittest.mock import MagicMock, PropertyMock, call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.media_player import DOMAIN as MP_DOMAIN
from homeassistant.components.yamaha import media_player as yamaha
from homeassistant.components.yamaha.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.setup import async_setup_component

from tests.components.yamaha._fixtures import (
    FakeYamahaDevice,
    device as device_fx,
    device2 as device2_fx,
    main_zone as main_zone_fx,
)
from tests.hass_fixtures import (
    caplog as caplog_fx,
    hass as hass_fixture,
    mock_network,
)

CONFIG = {"media_player": {"platform": "yamaha", "host": "127.0.0.1"}}


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@test
async def setup_host(
    hass: HomeAssistant = Depends(hass_fixture),
    device: FakeYamahaDevice = Depends(device_fx),
    device2: FakeYamahaDevice = Depends(device2_fx),
    main_zone: MagicMock = Depends(main_zone_fx),
) -> None:
    """Test set up integration with host."""
    expect(await async_setup_component(hass, MP_DOMAIN, CONFIG)).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get("media_player.yamaha_receiver_main_zone")

    expect(state is not None).to_be_truthy()
    expect(state.state).to_equal("off")

    with patch("rxv.find", return_value=[device2]):
        expect(await async_setup_component(hass, MP_DOMAIN, CONFIG)).to_be_truthy()
        await hass.async_block_till_done()

    state = hass.states.get("media_player.yamaha_receiver_main_zone")

    expect(state is not None).to_be_truthy()
    expect(state.state).to_equal("off")


@test.cases(
    test.case("attribute_error", error=AttributeError),
    test.case("value_error", error=ValueError),
    test.case("unicode_decode_error", error=UnicodeDecodeError("", b"", 1, 0, "")),
)
async def setup_find_errors(
    error: type[Exception] | Exception,
    hass: HomeAssistant = Depends(hass_fixture),
    device: FakeYamahaDevice = Depends(device_fx),
    main_zone: MagicMock = Depends(main_zone_fx),
) -> None:
    """Test set up integration encountering an Error."""
    with patch("rxv.find", side_effect=error):
        expect(await async_setup_component(hass, MP_DOMAIN, CONFIG)).to_be_truthy()
        await hass.async_block_till_done()

        state = hass.states.get("media_player.yamaha_receiver_main_zone")

        expect(state is not None).to_be_truthy()
        expect(state.state).to_equal("off")


@test
async def setup_no_host(
    hass: HomeAssistant = Depends(hass_fixture),
    device: FakeYamahaDevice = Depends(device_fx),
    main_zone: MagicMock = Depends(main_zone_fx),
) -> None:
    """Test set up integration without host."""
    with patch("rxv.find", return_value=[device]):
        expect(
            await async_setup_component(
                hass, MP_DOMAIN, {"media_player": {"platform": "yamaha"}}
            )
        ).to_be_truthy()
        await hass.async_block_till_done()

    state = hass.states.get("media_player.yamaha_receiver_main_zone")

    expect(state is not None).to_be_truthy()
    expect(state.state).to_equal("off")


@test
async def setup_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    device: FakeYamahaDevice = Depends(device_fx),
    main_zone: MagicMock = Depends(main_zone_fx),
) -> None:
    """Test set up integration via discovery."""
    discovery_info = {
        "name": "Yamaha Receiver",
        "model_name": "Yamaha",
        "control_url": "http://receiver",
        "description_url": "http://receiver/description",
    }
    await async_load_platform(
        hass, MP_DOMAIN, "yamaha", discovery_info, {MP_DOMAIN: {}}
    )
    await hass.async_block_till_done()

    state = hass.states.get("media_player.yamaha_receiver_main_zone")

    expect(state is not None).to_be_truthy()
    expect(state.state).to_equal("off")


@test
async def setup_zone_ignore(
    hass: HomeAssistant = Depends(hass_fixture),
    device: FakeYamahaDevice = Depends(device_fx),
    main_zone: MagicMock = Depends(main_zone_fx),
) -> None:
    """Test set up integration without host."""
    expect(
        await async_setup_component(
            hass,
            MP_DOMAIN,
            {
                "media_player": {
                    "platform": "yamaha",
                    "host": "127.0.0.1",
                    "zone_ignore": "Main zone",
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get("media_player.yamaha_receiver_main_zone")

    expect(state is None).to_be_truthy()


@test
async def enable_output(
    hass: HomeAssistant = Depends(hass_fixture),
    device: FakeYamahaDevice = Depends(device_fx),
    main_zone: MagicMock = Depends(main_zone_fx),
) -> None:
    """Test enable output service."""
    expect(await async_setup_component(hass, MP_DOMAIN, CONFIG)).to_be_truthy()
    await hass.async_block_till_done()

    port = "hdmi1"
    enabled = True
    data = {
        "entity_id": "media_player.yamaha_receiver_main_zone",
        "port": port,
        "enabled": enabled,
    }

    await hass.services.async_call(DOMAIN, yamaha.SERVICE_ENABLE_OUTPUT, data, True)

    expect(main_zone.enable_output.call_count).to_equal(1)
    expect(main_zone.enable_output.call_args).to_equal(call(port, enabled))


@test.cases(
    test.case("down", cursor=yamaha.CURSOR_TYPE_DOWN, method="menu_down"),
    test.case("left", cursor=yamaha.CURSOR_TYPE_LEFT, method="menu_left"),
    test.case("return", cursor=yamaha.CURSOR_TYPE_RETURN, method="menu_return"),
    test.case("right", cursor=yamaha.CURSOR_TYPE_RIGHT, method="menu_right"),
    test.case("select", cursor=yamaha.CURSOR_TYPE_SELECT, method="menu_sel"),
    test.case("up", cursor=yamaha.CURSOR_TYPE_UP, method="menu_up"),
)
async def menu_cursor(
    cursor: str,
    method: str,
    hass: HomeAssistant = Depends(hass_fixture),
    device: FakeYamahaDevice = Depends(device_fx),
    main_zone: MagicMock = Depends(main_zone_fx),
) -> None:
    """Verify that the correct menu method is called for the menu_cursor service."""
    expect(await async_setup_component(hass, MP_DOMAIN, CONFIG)).to_be_truthy()
    await hass.async_block_till_done()

    data = {
        "entity_id": "media_player.yamaha_receiver_main_zone",
        "cursor": cursor,
    }
    await hass.services.async_call(DOMAIN, yamaha.SERVICE_MENU_CURSOR, data, True)

    getattr(main_zone, method).assert_called_once_with()


@test
async def select_scene(
    hass: HomeAssistant = Depends(hass_fixture),
    device: FakeYamahaDevice = Depends(device_fx),
    main_zone: MagicMock = Depends(main_zone_fx),
    caplog=Depends(caplog_fx),
) -> None:
    """Test select scene service."""
    scene_prop = PropertyMock(return_value=None)
    type(main_zone).scene = scene_prop

    expect(await async_setup_component(hass, MP_DOMAIN, CONFIG)).to_be_truthy()
    await hass.async_block_till_done()

    scene = "TV Viewing"
    data = {
        "entity_id": "media_player.yamaha_receiver_main_zone",
        "scene": scene,
    }

    await hass.services.async_call(DOMAIN, yamaha.SERVICE_SELECT_SCENE, data, True)

    expect(scene_prop.call_count).to_equal(1)
    expect(scene_prop.call_args).to_equal(call(scene))

    scene = "BD/DVD Movie Viewing"
    data["scene"] = scene

    await hass.services.async_call(DOMAIN, yamaha.SERVICE_SELECT_SCENE, data, True)

    expect(scene_prop.call_count).to_equal(2)
    expect(scene_prop.call_args).to_equal(call(scene))

    scene_prop.side_effect = AssertionError()

    missing_scene = "Missing scene"
    data["scene"] = missing_scene

    await hass.services.async_call(DOMAIN, yamaha.SERVICE_SELECT_SCENE, data, True)

    expect(f"Scene '{missing_scene}' does not exist!" in caplog.text).to_be_truthy()
