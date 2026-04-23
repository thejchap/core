"""The config flow tests for the forked_daapd media player platform."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.forked_daapd.const import (
    CONF_LIBRESPOT_JAVA_PORT,
    CONF_MAX_PLAYLISTS,
    CONF_TTS_PAUSE_TIME,
    CONF_TTS_VOLUME,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.forked_daapd._fixtures import config_entry
from tests.hass_fixtures import hass as hass_fixture, mock_network

SAMPLE_CONFIG = {
    "websocket_port": 3688,
    "version": "25.0",
    "buildoptions": [
        "ffmpeg",
        "iTunes XML",
        "Spotify",
        "LastFM",
        "MPD",
        "Device verification",
        "Websockets",
        "ALSA",
    ],
}


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"
        ),
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
async def show_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def config_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test that the user step works."""
    with (
        patch(
            "homeassistant.components.forked_daapd.config_flow.ForkedDaapdAPI.test_connection",
            new=AsyncMock(),
        ) as mock_test_connection,
        patch(
            "homeassistant.components.forked_daapd.ForkedDaapdAPI.get_request",
            autospec=True,
        ) as mock_get_request,
        patch(
            "homeassistant.components.forked_daapd.async_setup_entry",
            return_value=True,
        ),
    ):
        mock_get_request.return_value = SAMPLE_CONFIG
        mock_test_connection.return_value = ["ok", "My Music on myhost"]
        config_data = config_entry.data
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=config_data
        )
        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("My Music on myhost")
        expect(result["data"][CONF_HOST]).to_equal(config_data[CONF_HOST])
        expect(result["data"][CONF_PORT]).to_equal(config_data[CONF_PORT])
        expect(result["data"][CONF_PASSWORD]).to_equal(config_data[CONF_PASSWORD])

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=config_entry.data,
        )
        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def zeroconf_updates_title(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test that zeroconf updates title and aborts with same host."""
    MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "different host"}).add_to_hass(hass)
    config_entry.add_to_hass(hass)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(2)
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.1"),
        ip_addresses=[ip_address("192.168.1.1")],
        hostname="mock_hostname",
        name="mock_name",
        port=23,
        properties={"mtd-version": "27.0", "Machine Name": "zeroconf_test"},
        type="mock_type",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(config_entry.title).to_equal("zeroconf_test")
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(2)


@test
async def config_flow_no_websocket(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test config flow setup without websocket enabled on server."""
    with patch(
        "homeassistant.components.forked_daapd.config_flow.ForkedDaapdAPI.test_connection",
        new=AsyncMock(),
    ) as mock_test_connection:
        mock_test_connection.return_value = ["websocket_not_enabled"]
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=config_entry.data
        )
        expect(result["type"]).to_be(FlowResultType.FORM)


@test.cases(
    test.case(
        "no_properties",
        properties={},
    ),
    test.case(
        "version_too_old",
        properties={"mtd-version": "26.3", "Machine Name": "forked-daapd"},
    ),
    test.case(
        "firefly_verbose_version",
        properties={"mtd-version": "0.2.4.1", "Machine Name": "firefly"},
    ),
    test.case(
        "firefly_svn_version",
        properties={"mtd-version": "svn-1676", "Machine Name": "firefly"},
    ),
)
async def config_flow_zeroconf_invalid(
    properties: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that an invalid zeroconf entry doesn't work."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("127.0.0.1"),
        ip_addresses=[ip_address("127.0.0.1")],
        hostname="mock_hostname",
        name="mock_name",
        port=23,
        properties=properties,
        type="mock_type",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_forked_daapd")


@test
async def config_flow_zeroconf_valid(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that a valid zeroconf entry works."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.1"),
        ip_addresses=[ip_address("192.168.1.1")],
        hostname="mock_hostname",
        name="mock_name",
        port=23,
        properties={
            "mtd-version": "27.0",
            "Machine Name": "zeroconf_test",
            "Machine ID": "5E55EEFF",
        },
        type="mock_type",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test config flow options."""
    with (
        patch(
            "homeassistant.components.forked_daapd.ForkedDaapdAPI.get_request",
            autospec=True,
        ) as mock_get_request,
        patch(
            "homeassistant.components.forked_daapd.async_setup_entry",
            return_value=True,
        ),
    ):
        mock_get_request.return_value = SAMPLE_CONFIG
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_TTS_PAUSE_TIME: 0.05,
                CONF_TTS_VOLUME: 0.8,
                CONF_LIBRESPOT_JAVA_PORT: 0,
                CONF_MAX_PLAYLISTS: 8,
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
