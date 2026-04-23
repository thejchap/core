"""Test the Hegel config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.hegel.const import CONF_MODEL, DOMAIN
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from .const import TEST_HOST, TEST_MODEL, TEST_UDN

from tests.common import MockConfigEntry
from tests.components.hegel._fixtures import (
    mock_config_entry,
    mock_hegel_client,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_NAME = "Hegel H190"
TEST_SSDP_LOCATION = f"http://{TEST_HOST}:8080/description.xml"


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: MagicMock = Depends(mock_setup_entry),
    _mock_hegel_client: MagicMock = Depends(mock_hegel_client),
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_MODEL: TEST_MODEL},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Hegel {TEST_MODEL}")
    expect(result["data"]).to_equal({CONF_HOST: TEST_HOST, CONF_MODEL: TEST_MODEL})


@test
async def user_flow_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: MagicMock = Depends(mock_setup_entry),
    mock_hegel_client: MagicMock = Depends(mock_hegel_client),
) -> None:
    """Test user flow when connection fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_hegel_client.ensure_connected.side_effect = OSError("Connection refused")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_MODEL: TEST_MODEL},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_hegel_client.ensure_connected.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_MODEL: TEST_MODEL},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user flow aborts when device is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST, CONF_MODEL: TEST_MODEL},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_discovery_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: MagicMock = Depends(mock_setup_entry),
    _mock_hegel_client: MagicMock = Depends(mock_hegel_client),
) -> None:
    """Test successful SSDP discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_udn=TEST_UDN,
            ssdp_location=TEST_SSDP_LOCATION,
            upnp={
                "presentationURL": f"http://{TEST_HOST}/",
                "friendlyName": TEST_NAME,
                "modelName": TEST_MODEL,
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MODEL: TEST_MODEL}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal({CONF_HOST: TEST_HOST, CONF_MODEL: TEST_MODEL})
    expect(result["result"].unique_id).to_equal(TEST_UDN)


@test
async def ssdp_discovery_from_ssdp_location(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: MagicMock = Depends(mock_setup_entry),
    _mock_hegel_client: MagicMock = Depends(mock_hegel_client),
) -> None:
    """Test SSDP discovery extracts host from ssdp_location when presentationURL is not available."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_udn=TEST_UDN,
            ssdp_location=TEST_SSDP_LOCATION,
            upnp={"friendlyName": TEST_NAME, "modelName": TEST_MODEL},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MODEL: TEST_MODEL}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal({CONF_HOST: TEST_HOST, CONF_MODEL: TEST_MODEL})


@test
async def ssdp_discovery_no_host(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test SSDP discovery aborts when no host can be determined."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_udn=TEST_UDN,
            ssdp_location="",
            upnp={},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_host_found")


@test
async def ssdp_discovery_no_udn(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test SSDP discovery aborts when no UDN is available."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=TEST_SSDP_LOCATION,
            upnp={
                "presentationURL": f"http://{TEST_HOST}/",
                "friendlyName": TEST_NAME,
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_host_found")


@test
async def ssdp_discovery_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test SSDP discovery aborts when device is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_udn=TEST_UDN,
            ssdp_location=TEST_SSDP_LOCATION,
            upnp={
                "presentationURL": f"http://{TEST_HOST}/",
                "friendlyName": TEST_NAME,
                "modelName": TEST_MODEL,
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_discovery_already_configured_updates_host(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_hegel_client: MagicMock = Depends(mock_hegel_client),
) -> None:
    """Test SSDP discovery updates host when device is already configured with different IP."""
    new_host = "192.168.1.50"

    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_udn=TEST_UDN,
            ssdp_location=f"http://{new_host}:8080/description.xml",
            upnp={
                "presentationURL": f"http://{new_host}/",
                "friendlyName": TEST_NAME,
                "modelName": TEST_MODEL,
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(mock_config_entry.data[CONF_HOST]).to_equal(new_host)


@test
async def ssdp_discovery_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_hegel_client: MagicMock = Depends(mock_hegel_client),
) -> None:
    """Test SSDP discovery aborts when connection fails."""
    mock_hegel_client.ensure_connected.side_effect = OSError("Connection refused")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_udn=TEST_UDN,
            ssdp_location=TEST_SSDP_LOCATION,
            upnp={
                "presentationURL": f"http://{TEST_HOST}/",
                "friendlyName": TEST_NAME,
                "modelName": TEST_MODEL,
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def ssdp_discovery_unknown_model(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_hegel_client: MagicMock = Depends(mock_hegel_client),
) -> None:
    """Test SSDP discovery with unknown model falls back to first model in list."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_udn=TEST_UDN,
            ssdp_location=TEST_SSDP_LOCATION,
            upnp={
                "presentationURL": f"http://{TEST_HOST}/",
                "friendlyName": "Hegel Unknown",
                "modelName": "UnknownModel",
            },
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")


@test
async def ssdp_discovery_multiple_services_same_device(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_hegel_client: MagicMock = Depends(mock_hegel_client),
) -> None:
    """Test that multiple SSDP discoveries from same device result in single discovery."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn=f"{TEST_UDN}::urn:schemas-upnp-org:service:RenderingControl:1",
            ssdp_st="urn:schemas-upnp-org:service:RenderingControl:1",
            ssdp_udn=TEST_UDN,
            ssdp_location=TEST_SSDP_LOCATION,
            upnp={
                "presentationURL": f"http://{TEST_HOST}/",
                "friendlyName": TEST_NAME,
                "modelName": TEST_MODEL,
            },
        ),
    )

    expect(result1["type"]).to_be(FlowResultType.FORM)
    expect(result1["step_id"]).to_equal("discovery_confirm")
    flow_id = result1["flow_id"]

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn=f"{TEST_UDN}::urn:schemas-upnp-org:service:AVTransport:1",
            ssdp_st="urn:schemas-upnp-org:service:AVTransport:1",
            ssdp_udn=TEST_UDN,
            ssdp_location=TEST_SSDP_LOCATION,
            upnp={
                "presentationURL": f"http://{TEST_HOST}/",
                "friendlyName": TEST_NAME,
                "modelName": TEST_MODEL,
            },
        ),
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_in_progress")

    flows = hass.config_entries.flow.async_progress()
    expect(len([f for f in flows if f["flow_id"] == flow_id])).to_equal(1)
