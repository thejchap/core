"""Test the Wyoming config flow."""

from ipaddress import IPv4Address
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test
from wyoming.info import Info

from homeassistant import config_entries
from homeassistant.components.wyoming.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.hassio import HassioServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import EMPTY_INFO, SATELLITE_INFO, STT_INFO, TTS_INFO
from ._fixtures import init_components, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

ADDON_DISCOVERY = HassioServiceInfo(
    config={
        "addon": "Piper",
        "uri": "tcp://mock-piper:10200",
    },
    name="Piper",
    slug="mock_piper",
    uuid="1234",
)

ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=IPv4Address("127.0.0.1"),
    ip_addresses=[IPv4Address("127.0.0.1")],
    port=12345,
    hostname="localhost",
    type="_wyoming._tcp.local.",
    name="test_zeroconf_name._wyoming._tcp.local.",
    properties={},
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _components: None = Depends(init_components),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures."""


@test
async def form_stt(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=STT_INFO,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "port": 1234},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Test ASR")
    expect(result2["data"]).to_equal({"host": "1.1.1.1", "port": 1234})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_tts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=TTS_INFO,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "port": 1234},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Test TTS")
    expect(result2["data"]).to_equal({"host": "1.1.1.1", "port": 1234})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "port": 1234},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def no_supported_services(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle no supported services error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=EMPTY_INFO,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1", "port": 1234},
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("no_services")


@test.cases(
    test.case("stt", info=STT_INFO),
    test.case("tts", info=TTS_INFO),
)
async def hassio_addon_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    info: Info,
) -> None:
    """Test config flow initiated by Supervisor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_DISCOVERY,
        context={"source": config_entries.SOURCE_HASSIO},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("hassio_confirm")
    expect(result.get("description_placeholders")).to_equal({"addon": "Piper"})

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=info,
    ) as mock_wyoming:
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_wyoming.mock_calls)).to_equal(1)


@test
async def hassio_addon_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort discovery if the add-on is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "mock-piper", "port": 10200},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_DISCOVERY,
        context={"source": config_entries.SOURCE_HASSIO},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
    expect(entry.unique_id).to_equal("1234")


@test
async def hassio_addon_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_DISCOVERY,
        context={"source": config_entries.SOURCE_HASSIO},
    )

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "cannot_connect"})


@test
async def hassio_addon_no_supported_services(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle no supported services error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_DISCOVERY,
        context={"source": config_entries.SOURCE_HASSIO},
    )

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=EMPTY_INFO,
    ):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("no_services")


@test
async def zeroconf_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow initiated by Supervisor."""
    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=SATELLITE_INFO,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=ZEROCONF_DISCOVERY,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("zeroconf_confirm")
    expect(result.get("description_placeholders")).to_equal(
        {"name": SATELLITE_INFO.satellite.name}
    )

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zeroconf_discovery_no_port(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery when the zeroconf service does not have a port."""
    with (
        patch(
            "homeassistant.components.wyoming.data.load_wyoming_info",
            return_value=SATELLITE_INFO,
        ),
        patch.object(ZEROCONF_DISCOVERY, "port", None),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=ZEROCONF_DISCOVERY,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("no_port")


@test
async def zeroconf_discovery_no_services(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery when there are no supported services on the client."""
    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=Info(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=ZEROCONF_DISCOVERY,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("no_services")


@test
async def zeroconf_discovery_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow initiated by Supervisor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "127.0.0.1", "port": 12345},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=SATELLITE_INFO,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=ZEROCONF_DISCOVERY,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(entry.unique_id).to_equal(
        "test_zeroconf_name._wyoming._tcp.local._Test Satellite"
    )


@test
async def bad_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can continue if a config entry is missing info."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_DISCOVERY,
        context={"source": config_entries.SOURCE_HASSIO},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=SATELLITE_INFO,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=ZEROCONF_DISCOVERY,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )
        expect(result.get("type")).to_be(FlowResultType.FORM)
