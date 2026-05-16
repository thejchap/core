"""Test Volvo services."""

from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, HTTPError, HTTPStatusError, Request, Response
from tryke import Depends, expect, fixture, test
from volvocarsapi.api import VolvoCarsApi

from homeassistant.components.volvo.const import DOMAIN
from homeassistant.components.volvo.services import (
    CONF_CONFIG_ENTRY_ID,
    CONF_IMAGE_TYPES,
    SERVICE_GET_IMAGE_URL,
    _async_image_exists,
    _parse_exterior_image_url,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from ._fixtures import (
    mock_api as mock_api_fx,
    mock_config_entry as mock_config_entry_fx,
    setup_integration as setup_integration_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Force tryke to run tests through the async executor."""
    return 0


@test
async def setup_services(
    hass: HomeAssistant = Depends(hass_fx),
    _api: VolvoCarsApi = Depends(mock_api_fx),
    setup_integration: Callable[[], Awaitable[bool]] = Depends(setup_integration_fx),
) -> None:
    """Test setup of services."""
    expect(await setup_integration()).to_be_truthy()

    services = hass.services.async_services_for_domain(DOMAIN)
    expect(services).to_be_truthy()
    expect(SERVICE_GET_IMAGE_URL in services).to_be_truthy()


@test
async def get_image_url_all(
    hass: HomeAssistant = Depends(hass_fx),
    _api: VolvoCarsApi = Depends(mock_api_fx),
    setup_integration: Callable[[], Awaitable[bool]] = Depends(setup_integration_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test if get_image_url returns all image types."""
    expect(await setup_integration()).to_be_truthy()

    with patch(
        "homeassistant.components.volvo.services._async_image_exists",
        new=AsyncMock(return_value=True),
    ):
        images = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_IMAGE_URL,
            {
                CONF_CONFIG_ENTRY_ID: mock_config_entry.entry_id,
                CONF_IMAGE_TYPES: [],
            },
            blocking=True,
            return_response=True,
        )

        expect(images).to_be_truthy()
        expect(images["images"]).to_be_truthy()
        expect(isinstance(images["images"], list)).to_be_truthy()
        expect(len(images["images"])).to_equal(9)


@test.cases(
    test.case("exterior_back", image_type="exterior_back"),
    test.case("exterior_back_left", image_type="exterior_back_left"),
    test.case("exterior_back_right", image_type="exterior_back_right"),
    test.case("exterior_front", image_type="exterior_front"),
    test.case("exterior_front_left", image_type="exterior_front_left"),
    test.case("exterior_front_right", image_type="exterior_front_right"),
    test.case("exterior_side_left", image_type="exterior_side_left"),
    test.case("exterior_side_right", image_type="exterior_side_right"),
    test.case("interior", image_type="interior"),
)
async def get_image_url_selected(
    image_type: str,
    hass: HomeAssistant = Depends(hass_fx),
    _api: VolvoCarsApi = Depends(mock_api_fx),
    setup_integration: Callable[[], Awaitable[bool]] = Depends(setup_integration_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test if get_image_url returns selected image types."""
    expect(await setup_integration()).to_be_truthy()

    with patch(
        "homeassistant.components.volvo.services._async_image_exists",
        new=AsyncMock(return_value=True),
    ):
        images = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_IMAGE_URL,
            {
                CONF_CONFIG_ENTRY_ID: mock_config_entry.entry_id,
                CONF_IMAGE_TYPES: [image_type],
            },
            blocking=True,
            return_response=True,
        )

        expect(images).to_be_truthy()
        expect(images["images"]).to_be_truthy()
        expect(isinstance(images["images"], list)).to_be_truthy()
        expect(len(images["images"])).to_equal(1)


@test.cases(
    test.case("empty", entry_id="", translation_key="invalid_entry_id"),
    test.case("fake", entry_id="fake_entry_id", translation_key="invalid_entry"),
    test.case("wrong", entry_id="wrong_entry_id", translation_key="entry_not_found"),
)
async def invalid_config_entry(
    entry_id: str,
    translation_key: str,
    hass: HomeAssistant = Depends(hass_fx),
    _api: VolvoCarsApi = Depends(mock_api_fx),
    setup_integration: Callable[[], Awaitable[bool]] = Depends(setup_integration_fx),
) -> None:
    """Test invalid config entry parameters."""
    expect(await setup_integration()).to_be_truthy()

    config_entry = MockConfigEntry(domain="fake_entry", entry_id="fake_entry_id")
    config_entry.add_to_hass(hass)

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_IMAGE_URL,
            {
                CONF_CONFIG_ENTRY_ID: entry_id,
                CONF_IMAGE_TYPES: [],
            },
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal(translation_key)


@test
async def invalid_image_type(
    hass: HomeAssistant = Depends(hass_fx),
    _api: VolvoCarsApi = Depends(mock_api_fx),
    setup_integration: Callable[[], Awaitable[bool]] = Depends(setup_integration_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test invalid image type parameters."""
    expect(await setup_integration()).to_be_truthy()

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_IMAGE_URL,
            {
                CONF_CONFIG_ENTRY_ID: mock_config_entry.entry_id,
                CONF_IMAGE_TYPES: ["top"],
            },
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("invalid_image_type")


@test
async def async_image_exists(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test _async_image_exists returns True on successful response."""
    client = AsyncMock(spec=AsyncClient)
    response = AsyncMock()
    response.raise_for_status = MagicMock(return_value=None)
    client.stream().__aenter__.return_value = response

    expect(
        await _async_image_exists(client, "http://example.com/image.jpg")
    ).to_be_truthy()


@test
async def async_image_does_not_exist(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test _async_image_exists returns False when image does not exist."""
    client = AsyncMock(spec=AsyncClient)
    client.stream.side_effect = HTTPStatusError(
        "Not found",
        request=Request("GET", "http://example.com"),
        response=Response(status_code=404),
    )

    expect(
        await _async_image_exists(client, "http://example.com/image.jpg")
    ).to_be_falsy()


@test
async def async_image_non_404_status_error(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test _async_image_exists raises HomeAssistantError on non-404 HTTP status errors."""
    client = AsyncMock(spec=AsyncClient)
    client.stream.side_effect = HTTPStatusError(
        "Internal server error",
        request=Request("GET", "http://example.com"),
        response=Response(status_code=500),
    )

    raised: HomeAssistantError | None = None
    try:
        await _async_image_exists(client, "http://example.com/image.jpg")
    except HomeAssistantError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("image_error")


@test
async def async_image_error(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test _async_image_exists raises."""
    client = AsyncMock(spec=AsyncClient)
    client.stream.side_effect = HTTPError("HTTP error")

    raised: HomeAssistantError | None = None
    try:
        await _async_image_exists(client, "http://example.com/image.jpg")
    except HomeAssistantError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("image_error")


@test
def parse_exterior_image_url_wizz_valid_angle() -> None:
    """Replace angle segment in wizz-hosted URL when angle is valid."""
    src = "https://wizz.images.volvocars.com/images/threeQuartersRearLeft/abc123.jpg"
    result = _parse_exterior_image_url(src, "6")
    expect(result).to_equal(
        "https://wizz.images.volvocars.com/images/rear/abc123.jpg"
    )


@test
def parse_exterior_image_url_wizz_invalid_angle() -> None:
    """Return empty string for wizz-hosted URL when angle is invalid."""
    src = "https://wizz.images.volvocars.com/images/front/xyz.jpg"
    expect(_parse_exterior_image_url(src, "9")).to_equal("")


@test
def parse_exterior_image_url_non_wizz_sets_angle() -> None:
    """Add angle query to non-wizz URL."""
    src = "https://images.volvocars.com/image?foo=bar&angle=1"
    result = _parse_exterior_image_url(src, "3")
    expect("angle=3" in result).to_be_truthy()
