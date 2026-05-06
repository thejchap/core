"""Tests for the IPP config flow."""

import dataclasses
from ipaddress import ip_address
import json
from unittest.mock import AsyncMock, MagicMock, patch

from pyipp import (
    IPPConnectionError,
    IPPConnectionUpgradeRequired,
    IPPError,
    IPPParseError,
    IPPVersionNotSupportedError,
    Printer,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.ipp.const import CONF_BASE_PATH, DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SSL, CONF_UUID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    MOCK_USER_INPUT,
    MOCK_ZEROCONF_IPP_SERVICE_INFO,
    MOCK_ZEROCONF_IPPS_SERVICE_INFO,
)

from tests.common import MockConfigEntry, load_fixture
from tests.components.ipp._fixtures import (
    mock_config_entry,
    mock_ipp_config_flow,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


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
async def show_user_form(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def show_zeroconf_form(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test that the zeroconf confirmation form is served."""
    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["description_placeholders"]).to_equal(
        {CONF_NAME: "EPSON XP-6000 Series"}
    )


@test.cases(
    test.case(
        "connection_error",
        exc=IPPConnectionError,
        source=SOURCE_USER,
        expected_type=FlowResultType.FORM,
        expected_step="user",
        expected_errors={"base": "cannot_connect"},
        expected_reason=None,
    ),
    test.case(
        "zeroconf_connection_error",
        exc=IPPConnectionError,
        source=SOURCE_ZEROCONF,
        expected_type=FlowResultType.ABORT,
        expected_step=None,
        expected_errors=None,
        expected_reason="cannot_connect",
    ),
    test.case(
        "user_connection_upgrade_required",
        exc=IPPConnectionUpgradeRequired,
        source=SOURCE_USER,
        expected_type=FlowResultType.FORM,
        expected_step="user",
        expected_errors={"base": "connection_upgrade"},
        expected_reason=None,
    ),
    test.case(
        "zeroconf_connection_upgrade_required",
        exc=IPPConnectionUpgradeRequired,
        source=SOURCE_ZEROCONF,
        expected_type=FlowResultType.ABORT,
        expected_step=None,
        expected_errors=None,
        expected_reason="connection_upgrade",
    ),
    test.case(
        "user_parse_error",
        exc=IPPParseError,
        source=SOURCE_USER,
        expected_type=FlowResultType.ABORT,
        expected_step=None,
        expected_errors=None,
        expected_reason="parse_error",
    ),
    test.case(
        "zeroconf_parse_error",
        exc=IPPParseError,
        source=SOURCE_ZEROCONF,
        expected_type=FlowResultType.ABORT,
        expected_step=None,
        expected_errors=None,
        expected_reason="parse_error",
    ),
    test.case(
        "user_ipp_error",
        exc=IPPError,
        source=SOURCE_USER,
        expected_type=FlowResultType.ABORT,
        expected_step=None,
        expected_errors=None,
        expected_reason="ipp_error",
    ),
    test.case(
        "zeroconf_ipp_error",
        exc=IPPError,
        source=SOURCE_ZEROCONF,
        expected_type=FlowResultType.ABORT,
        expected_step=None,
        expected_errors=None,
        expected_reason="ipp_error",
    ),
    test.case(
        "user_ipp_version_error",
        exc=IPPVersionNotSupportedError,
        source=SOURCE_USER,
        expected_type=FlowResultType.ABORT,
        expected_step=None,
        expected_errors=None,
        expected_reason="ipp_version_error",
    ),
    test.case(
        "zeroconf_ipp_version_error",
        exc=IPPVersionNotSupportedError,
        source=SOURCE_ZEROCONF,
        expected_type=FlowResultType.ABORT,
        expected_step=None,
        expected_errors=None,
        expected_reason="ipp_version_error",
    ),
)
async def init_errors(
    exc: type[Exception],
    source: str,
    expected_type: FlowResultType,
    expected_step: str | None,
    expected_errors: dict | None,
    expected_reason: str | None,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test error handling during init."""
    mock_ipp_config_flow.printer.side_effect = exc

    data: dict | object
    if source == SOURCE_USER:
        data = MOCK_USER_INPUT.copy()
    else:
        data = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": source}, data=data
    )

    expect(result["type"]).to_be(expected_type)
    if expected_step is not None:
        expect(result["step_id"]).to_equal(expected_step)
    if expected_errors is not None:
        expect(result["errors"]).to_equal(expected_errors)
    if expected_reason is not None:
        expect(result["reason"]).to_equal(expected_reason)


@test
async def user_device_exists_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test we abort user flow if printer already configured."""
    mock_config_entry.add_to_hass(hass)

    user_input = MOCK_USER_INPUT.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=user_input,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_device_exists_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test we abort zeroconf flow if printer already configured."""
    mock_config_entry.add_to_hass(hass)

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_with_uuid_device_exists_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test we abort zeroconf flow if printer already configured."""
    mock_config_entry.add_to_hass(hass)

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)
    discovery_info.properties = {
        **MOCK_ZEROCONF_IPP_SERVICE_INFO.properties,
        "UUID": "cfe92100-67c4-11d4-a45f-f8d027761251",
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_with_uuid_device_exists_abort_new_host(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test we abort zeroconf flow if printer already configured, updating host."""
    mock_config_entry.add_to_hass(hass)

    discovery_info = dataclasses.replace(
        MOCK_ZEROCONF_IPP_SERVICE_INFO, ip_address=ip_address("1.2.3.9")
    )
    discovery_info.properties = {
        **MOCK_ZEROCONF_IPP_SERVICE_INFO.properties,
        "UUID": "cfe92100-67c4-11d4-a45f-f8d027761251",
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("1.2.3.9")


@test
async def zeroconf_empty_unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test zeroconf flow if printer lacks (empty) unique identification."""
    printer = mock_ipp_config_flow.printer.return_value
    printer.unique_id = None

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)
    discovery_info.properties = {
        **MOCK_ZEROCONF_IPP_SERVICE_INFO.properties,
        "UUID": "",
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.31", CONF_BASE_PATH: "/ipp/print"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("EPSON XP-6000 Series")

    expect(result["data"][CONF_HOST]).to_equal("192.168.1.31")
    expect(result["data"][CONF_UUID]).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")
    expect(result["result"].unique_id).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")


@test
async def zeroconf_no_unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test zeroconf flow if printer lacks unique identification."""
    printer = mock_ipp_config_flow.printer.return_value
    printer.unique_id = None

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.31", CONF_BASE_PATH: "/ipp/print"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("EPSON XP-6000 Series")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.31")
    expect(result["data"][CONF_UUID]).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")
    expect(result["result"].unique_id).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")


@test
async def full_user_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.31", CONF_BASE_PATH: "/ipp/print"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("192.168.1.31")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.31")
    expect(result["data"][CONF_UUID]).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")
    expect(result["result"].unique_id).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")


@test
async def full_zeroconf_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test the full zeroconf flow from start to finish."""
    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("EPSON XP-6000 Series")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.31")
    expect(result["data"][CONF_NAME]).to_equal("EPSON XP-6000 Series")
    expect(result["data"][CONF_UUID]).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")
    expect(bool(result["data"][CONF_SSL])).to_be(False)
    expect(result["result"].unique_id).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")


@test
async def full_zeroconf_tls_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_ipp_config_flow: MagicMock = Depends(mock_ipp_config_flow),
) -> None:
    """Test the full zeroconf TLS flow from start to finish."""
    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPPS_SERVICE_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["description_placeholders"]).to_equal(
        {CONF_NAME: "EPSON XP-6000 Series"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("EPSON XP-6000 Series")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.31")
    expect(result["data"][CONF_NAME]).to_equal("EPSON XP-6000 Series")
    expect(result["data"][CONF_UUID]).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")
    expect(bool(result["data"][CONF_SSL])).to_be(True)
    expect(result["result"].unique_id).to_equal("cfe92100-67c4-11d4-a45f-f8d027761251")


@test
async def zeroconf_empty_unique_id_uses_serial(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf flow if printer lacks (empty) unique id with serial fallback."""
    fixture = await hass.async_add_executor_job(
        load_fixture, "ipp/printer_without_uuid.json"
    )
    mock_printer_without_uuid = Printer.from_dict(json.loads(fixture))
    mock_printer_without_uuid.unique_id = None

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)
    discovery_info.properties = {
        **MOCK_ZEROCONF_IPP_SERVICE_INFO.properties,
        "UUID": "",
    }
    with patch(
        "homeassistant.components.ipp.config_flow.IPP", autospec=True
    ) as ipp_mock:
        client = ipp_mock.return_value
        client.printer.return_value = mock_printer_without_uuid
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_ZEROCONF},
            data=discovery_info,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.1.31", CONF_BASE_PATH: "/ipp/print"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("EPSON XP-6000 Series")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.31")
    expect(result["data"][CONF_UUID]).to_equal("")
    expect(result["result"].unique_id).to_equal("555534593035345555")
