"""Tests for the Amber config flow."""

from datetime import date
from unittest.mock import AsyncMock, Mock, patch

from amberelectric import ApiException
from amberelectric.models.site import Site
from amberelectric.models.site_status import SiteStatus
from tryke import Depends, expect, fixture, test

from homeassistant.components.amberelectric.config_flow import filter_sites
from homeassistant.components.amberelectric.const import (
    CONF_SITE_ID,
    CONF_SITE_NAME,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.amberelectric._fixtures import mock_setup_entry
from tests.hass_fixtures import hass, mock_network

API_KEY = "psk_123456789"


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


def _make_api(sites: list[Site] | None = None, side_effect: Exception | None = None) -> Mock:
    """Build a Mock AmberApi instance."""
    instance = Mock()
    if side_effect is not None:
        instance.get_sites.side_effect = side_effect
    else:
        instance.get_sites.return_value = sites or []
    return instance


@test
async def single_pending_site(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test single site."""
    site = Site(
        id="01FG0AGP818PXK0DWHXJRRT2DH",
        nmi="11111111111",
        channels=[],
        network="Jemena",
        status=SiteStatus.PENDING,
        active_from=None,
        closed_on=None,
        interval_length=30,
    )
    instance = _make_api(sites=[site])

    with patch("amberelectric.AmberApi", return_value=instance):
        initial_result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(initial_result.get("type") is FlowResultType.FORM).to_be(True)
        expect(initial_result.get("step_id")).to_equal("user")

        enter_api_key_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_API_TOKEN: API_KEY},
        )
        expect(enter_api_key_result.get("type") is FlowResultType.FORM).to_be(True)
        expect(enter_api_key_result.get("step_id")).to_equal("site")

        select_site_result = await hass.config_entries.flow.async_configure(
            enter_api_key_result["flow_id"],
            {CONF_SITE_ID: "01FG0AGP818PXK0DWHXJRRT2DH", CONF_SITE_NAME: "Home"},
        )

    expect(select_site_result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(select_site_result.get("title")).to_equal("Home")
    data = select_site_result.get("data")
    expect(data is not None).to_be(True)
    expect(data[CONF_API_TOKEN]).to_equal(API_KEY)
    expect(data[CONF_SITE_ID]).to_equal("01FG0AGP818PXK0DWHXJRRT2DH")


@test
async def single_site(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test single site."""
    site = Site(
        id="01FG0AGP818PXK0DWHXJRRT2DH",
        nmi="11111111111",
        channels=[],
        network="Jemena",
        status=SiteStatus.ACTIVE,
        active_from=date(2002, 1, 1),
        closed_on=None,
        interval_length=30,
    )
    instance = _make_api(sites=[site])

    with patch("amberelectric.AmberApi", return_value=instance):
        initial_result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(initial_result.get("type") is FlowResultType.FORM).to_be(True)
        expect(initial_result.get("step_id")).to_equal("user")

        enter_api_key_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_API_TOKEN: API_KEY},
        )
        expect(enter_api_key_result.get("type") is FlowResultType.FORM).to_be(True)
        expect(enter_api_key_result.get("step_id")).to_equal("site")

        select_site_result = await hass.config_entries.flow.async_configure(
            enter_api_key_result["flow_id"],
            {CONF_SITE_ID: "01FG0AGP818PXK0DWHXJRRT2DH", CONF_SITE_NAME: "Home"},
        )

    expect(select_site_result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(select_site_result.get("title")).to_equal("Home")
    data = select_site_result.get("data")
    expect(data is not None).to_be(True)
    expect(data[CONF_API_TOKEN]).to_equal(API_KEY)
    expect(data[CONF_SITE_ID]).to_equal("01FG0AGP818PXK0DWHXJRRT2DH")


@test
async def single_closed_site_no_closed_date(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test single closed site with no closed date."""
    site = Site(
        id="01FG0AGP818PXK0DWHXJRRT2DH",
        nmi="11111111111",
        channels=[],
        network="Jemena",
        status=SiteStatus.CLOSED,
        active_from=None,
        closed_on=None,
        interval_length=30,
    )
    instance = _make_api(sites=[site])

    with patch("amberelectric.AmberApi", return_value=instance):
        initial_result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(initial_result.get("type") is FlowResultType.FORM).to_be(True)
        expect(initial_result.get("step_id")).to_equal("user")

        enter_api_key_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_API_TOKEN: API_KEY},
        )
        expect(enter_api_key_result.get("type") is FlowResultType.FORM).to_be(True)
        expect(enter_api_key_result.get("step_id")).to_equal("site")

        select_site_result = await hass.config_entries.flow.async_configure(
            enter_api_key_result["flow_id"],
            {CONF_SITE_ID: "01FG0AGP818PXK0DWHXJRRT2DH", CONF_SITE_NAME: "Home"},
        )

    expect(select_site_result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(select_site_result.get("title")).to_equal("Home")
    data = select_site_result.get("data")
    expect(data is not None).to_be(True)
    expect(data[CONF_API_TOKEN]).to_equal(API_KEY)
    expect(data[CONF_SITE_ID]).to_equal("01FG0AGP818PXK0DWHXJRRT2DH")


def _rejoin_sites() -> list[Site]:
    site_1 = Site(
        id="01HGD9QB72HB3DWQNJ6SSCGXGV",
        nmi="11111111111",
        channels=[],
        network="Jemena",
        status=SiteStatus.CLOSED,
        active_from=date(2002, 1, 1),
        closed_on=date(2002, 6, 1),
        interval_length=30,
    )
    site_2 = Site(
        id="01FG0AGP818PXK0DWHXJRRT2DH",
        nmi="11111111111",
        channels=[],
        network="Jemena",
        status=SiteStatus.ACTIVE,
        active_from=date(2003, 1, 1),
        closed_on=None,
        interval_length=30,
    )
    site_3 = Site(
        id="01FG0AGP818PXK0DWHXJRRT2DH",
        nmi="11111111112",
        channels=[],
        network="Jemena",
        status=SiteStatus.CLOSED,
        active_from=date(2003, 1, 1),
        closed_on=date(2003, 6, 1),
        interval_length=30,
    )
    return [site_1, site_2, site_3]


@test
async def single_site_rejoin(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test single site rejoin."""
    instance = _make_api(sites=_rejoin_sites())

    with patch("amberelectric.AmberApi", return_value=instance):
        initial_result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(initial_result.get("type") is FlowResultType.FORM).to_be(True)
        expect(initial_result.get("step_id")).to_equal("user")

        enter_api_key_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_API_TOKEN: API_KEY},
        )
        expect(enter_api_key_result.get("type") is FlowResultType.FORM).to_be(True)
        expect(enter_api_key_result.get("step_id")).to_equal("site")

        select_site_result = await hass.config_entries.flow.async_configure(
            enter_api_key_result["flow_id"],
            {CONF_SITE_ID: "01FG0AGP818PXK0DWHXJRRT2DH", CONF_SITE_NAME: "Home"},
        )

    expect(select_site_result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(select_site_result.get("title")).to_equal("Home")
    data = select_site_result.get("data")
    expect(data is not None).to_be(True)
    expect(data[CONF_API_TOKEN]).to_equal(API_KEY)
    expect(data[CONF_SITE_ID]).to_equal("01FG0AGP818PXK0DWHXJRRT2DH")


@test
async def no_site(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test no site."""
    instance = _make_api(sites=[])

    with patch("amberelectric.AmberApi", return_value=instance):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_API_TOKEN: "psk_123456789"},
        )

    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({"api_token": "no_site"})


@test
async def invalid_key(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test invalid api key."""
    instance = _make_api(side_effect=ApiException(status=403))

    with patch("amberelectric.AmberApi", return_value=instance):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result.get("type") is FlowResultType.FORM).to_be(True)
        expect(result.get("step_id")).to_equal("user")

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_API_TOKEN: "psk_123456789"},
        )
    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({"api_token": "invalid_api_token"})


@test
async def unknown_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test unknown api error."""
    instance = _make_api(side_effect=ApiException(status=500))

    with patch("amberelectric.AmberApi", return_value=instance):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result.get("type") is FlowResultType.FORM).to_be(True)
        expect(result.get("step_id")).to_equal("user")

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_API_TOKEN: "psk_123456789"},
        )
    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({"api_token": "unknown_error"})


@test
async def site_deduplication() -> None:
    """Test site deduplication."""
    instance = _make_api(sites=_rejoin_sites())
    filtered = filter_sites(instance.get_sites())
    expect(len(filtered)).to_equal(2)
    expect(
        next(s for s in filtered if s.nmi == "11111111111").status == SiteStatus.ACTIVE
    ).to_be(True)
    expect(
        next(s for s in filtered if s.nmi == "11111111112").status == SiteStatus.CLOSED
    ).to_be(True)
