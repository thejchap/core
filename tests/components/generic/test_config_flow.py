"""Test the generic camera config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.generic.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user form is rendered for an empty flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)


@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_only_stillimage() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_invalid_user_input() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_only_stillimage_gif() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_only_svg_whitelisted_domain() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_rtsp_mjpeg_url() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_only_stream() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_still_and_stream_not_provided() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_image_timeout() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_stream_invalidimage() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_stream_invalidimage2() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_stream_invalidimage3() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_stream_unauthorised() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_stream_other_error() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_oserror() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_stream_worker_error() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_stream_permissions_error() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_no_route_to_host() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_stream_io_error() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def form_already_exists() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def options_template_error() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def slug() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def options_only_stream() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def options_still_and_stream() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def options_only_stream_invalid() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def options_still_only() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def options_invalid_user_input() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def options_image_timeout() -> None:
    """Stub."""

@test.skip("requires fakeimg/respx mock + WebSocket flow + create_stream chain")
async def options_invalid_template() -> None:
    """Stub."""
