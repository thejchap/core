"""Tests the Indevolt config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.indevolt.const import (
    CONF_GENERATION,
    CONF_SERIAL_NUMBER,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.indevolt._fixtures import (
    TEST_DEVICE_SN_GEN2,
    TEST_HOST,
    mock_config_entry,
    mock_indevolt,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_HOST_NEW = "192.168.1.200"


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
    _mock_indevolt: AsyncMock = Depends(mock_indevolt),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful user-initiated config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("INDEVOLT CMS-SF2000")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_SERIAL_NUMBER: TEST_DEVICE_SN_GEN2,
            CONF_MODEL: "CMS-SF2000",
            CONF_GENERATION: 2,
        }
    )
    expect(result["result"].unique_id).to_equal(TEST_DEVICE_SN_GEN2)


@test.cases(
    test.case("timeout", exception=TimeoutError, expected_error="timeout"),
    test.case("connection", exception=ConnectionError, expected_error="cannot_connect"),
    test.case("client", exception=ClientError, expected_error="cannot_connect"),
    test.case(
        "unknown", exception=Exception("Some unknown error"), expected_error="unknown"
    ),
)
async def user_flow_error(
    exception: type[Exception] | Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_indevolt: AsyncMock = Depends(mock_indevolt),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test connection errors in user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_indevolt.get_config.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(expected_error)

    mock_indevolt.get_config.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("INDEVOLT CMS-SF2000")


@test
async def user_flow_duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_indevolt: AsyncMock = Depends(mock_indevolt),
) -> None:
    """Test duplicate entry aborts the flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_indevolt: AsyncMock = Depends(mock_indevolt),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful reconfiguration flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_config_entry.entry_id},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    new_host = TEST_HOST_NEW
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: new_host}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    await hass.async_block_till_done()

    expect(mock_config_entry.data[CONF_HOST]).to_equal(new_host)
    expect(mock_config_entry.data[CONF_SERIAL_NUMBER]).to_equal(TEST_DEVICE_SN_GEN2)


@test.cases(
    test.case("timeout", exception=TimeoutError, expected_error="timeout"),
    test.case("connection", exception=ConnectionError, expected_error="cannot_connect"),
    test.case("client", exception=ClientError, expected_error="cannot_connect"),
    test.case(
        "unknown", exception=Exception("Some unknown error"), expected_error="unknown"
    ),
)
async def reconfigure_flow_error(
    exception: type[Exception] | Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_indevolt: AsyncMock = Depends(mock_indevolt),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test connection errors in reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_config_entry.entry_id},
    )

    mock_indevolt.get_config.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(expected_error)

    mock_indevolt.get_config.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    await hass.async_block_till_done()


@test
async def reconfigure_flow_different_device(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_indevolt: AsyncMock = Depends(mock_indevolt),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure aborts when connecting to a different device."""
    mock_config_entry.add_to_hass(hass)

    mock_indevolt.get_config.return_value = {
        "device": {
            "sn": "DIFFERENT-SERIAL-99999999",
            "type": "CMS-OTHER",
            "generation": 1,
            "fw": "1.0.0",
        }
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_config_entry.entry_id},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST_NEW}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("different_device")

    await hass.async_block_till_done()
