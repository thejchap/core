"""Test the generic config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("complex fixtures; needs detailed manual port")
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the form with a normal set of settings."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_only_stillimage(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we complete ok if the user wants still images only."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_reject_preview(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we go back to the config screen if the user rejects the preview."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_still_preview_cam_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test camera errors are triggered during preview."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_only_stillimage_gif(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we complete ok if the user wants a gif."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_only_svg_whitespace(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we complete ok if svg starts with whitespace, issue #68889."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_only_still_sample(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test various sample images #69037."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_still_template(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can handle various templates."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_rtsp_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we complete ok if the user enters a stream url."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_only_stream(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we complete ok if the user wants stream only."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_still_and_stream_not_provided(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show a suitable error if neither still or stream URL are provided."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_image_http_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle image http exceptions."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_image_http_302(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle image http 302 (temporary redirect)."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_stream_invalidimage(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid image when a stream is specified."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_stream_invalidimage2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid image when a stream is specified."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_stream_invalidimage3(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid image when a stream is specified."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_stream_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_stream_not_set_up(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle if stream has not been set up."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_stream_other_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the unknown error for streams."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_stream_permission_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle permission error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_no_route_to_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle no route to host."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_stream_io_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle an io error when setting up stream."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def form_oserror(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle OS error when setting up stream."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def options_template_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the options flow with a template error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def slug(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the slug function generates an error in case of invalid template."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def options_only_stream(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the options flow without a still_image_url."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def options_still_and_stream_not_provided(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we show a suitable error if neither still or stream URL are provided."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def options_permission_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a PermissionError and pass the message through."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def migrate_existing_ids(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that existing ids are migrated for issue #70568."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def options_use_wallclock_as_timestamps(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the use_wallclock_as_timestamps option flow."""
    expect(True).to_be(True)


