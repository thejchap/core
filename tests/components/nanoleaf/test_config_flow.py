"""Test the Nanoleaf config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

from aionanoleaf2 import InvalidToken, Unauthorized, Unavailable
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nanoleaf.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from homeassistant.helpers.service_info.zeroconf import (
    ATTR_PROPERTIES_ID,
    ZeroconfServiceInfo,
)

from tests.common import MockConfigEntry
from tests.components.nanoleaf._fixtures import mock_async_zeroconf
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_NAME = "Canvas ADF9"
TEST_HOST = "192.168.0.100"
TEST_OTHER_HOST = "192.168.0.200"
TEST_TOKEN = "R34F1c92FNv3pcZs4di17RxGqiLSwHM"
TEST_OTHER_TOKEN = "Qs4dxGcHR34l29RF1c92FgiLQBt3pcM"
TEST_DEVICE_ID = "5E:2E:EA:XX:XX:XX"
TEST_OTHER_DEVICE_ID = "5E:2E:EA:YY:YY:YY"


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _maz: MagicMock = Depends(mock_async_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


def _mock_nanoleaf(
    host: str = TEST_HOST,
    auth_token: str = TEST_TOKEN,
    authorize_error: Exception | None = None,
    get_info_error: Exception | None = None,
) -> MagicMock:
    nanoleaf = MagicMock()
    nanoleaf.name = TEST_NAME
    nanoleaf.host = host
    nanoleaf.auth_token = auth_token
    nanoleaf.authorize = AsyncMock(side_effect=authorize_error)
    nanoleaf.get_info = AsyncMock(side_effect=get_info_error)
    return nanoleaf


@test
async def user_unavailable_user_step_link_step(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle Unavailable in user and link step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize",
        side_effect=Unavailable,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
    expect(result2["last_step"]).to_be_falsy()

    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("link")

    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize",
        side_effect=Unavailable,
    ):
        result3 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("cannot_connect")


@test.cases(
    test.case("unavailable", Unavailable, "cannot_connect"),
    test.case("invalid_token", InvalidToken, "invalid_token"),
    test.case("exception", Exception, "unknown"),
)
async def user_error_setup_finish(
    error: type[Exception],
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test abort flow if on error in setup_finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize",
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("link")

    with (
        patch("homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize"),
        patch(
            "homeassistant.components.nanoleaf.config_flow.Nanoleaf.get_info",
            side_effect=error,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal(reason)


@test
async def user_not_authorizing_new_tokens_user_step_link_step(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle NotAuthorizingNewTokens in user step and link step."""
    with (
        patch(
            "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
            return_value=_mock_nanoleaf(authorize_error=Unauthorized()),
        ) as mock_nanoleaf,
        patch(
            "homeassistant.components.nanoleaf.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_be(None)
        expect(result["step_id"]).to_equal("user")
        expect(result["last_step"]).to_be_falsy()

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_be(None)
        expect(result2["step_id"]).to_equal("link")

        result3 = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result3["type"]).to_be(FlowResultType.FORM)
        expect(result3["errors"]).to_be(None)
        expect(result3["step_id"]).to_equal("link")

        result4 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result4["type"]).to_be(FlowResultType.FORM)
        expect(result4["errors"]).to_equal({"base": "not_allowing_new_tokens"})
        expect(result4["step_id"]).to_equal("link")

        mock_nanoleaf.return_value.authorize.side_effect = None

        result5 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result5["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result5["title"]).to_equal(TEST_NAME)
        expect(result5["data"]).to_equal(
            {CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN}
        )
        await hass.async_block_till_done()
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_exception_user_step(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle Exception errors in user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
        return_value=_mock_nanoleaf(authorize_error=Exception()),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "unknown"})
    expect(result2["last_step"]).to_be_falsy()

    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
        return_value=_mock_nanoleaf(),
    ) as mock_nanoleaf:
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )
        expect(result3["step_id"]).to_equal("link")

        mock_nanoleaf.return_value.authorize.side_effect = Exception()

        result4 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result4["type"]).to_be(FlowResultType.FORM)
        expect(result4["step_id"]).to_equal("link")
        expect(result4["errors"]).to_equal({"base": "unknown"})

        mock_nanoleaf.return_value.authorize.side_effect = None
        mock_nanoleaf.return_value.get_info.side_effect = Exception()
        result5 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result5["type"]).to_be(FlowResultType.ABORT)
    expect(result5["reason"]).to_equal("unknown")


@test.cases(
    test.case("homekit_hap", config_entries.SOURCE_HOMEKIT, "_hap._tcp.local"),
    test.case("zeroconf_ms", config_entries.SOURCE_ZEROCONF, "_nanoleafms._tcp.local"),
    test.case(
        "zeroconf_api", config_entries.SOURCE_ZEROCONF, "_nanoleafapi._tcp.local."
    ),
)
async def discovery_link_unavailable(
    source: str,
    type_in_discovery_info: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery and abort if device is unavailable."""
    with (
        patch("homeassistant.components.nanoleaf.config_flow.Nanoleaf.get_info"),
        patch(
            "homeassistant.components.nanoleaf.config_flow.load_json_object",
            return_value={},
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=ZeroconfServiceInfo(
                ip_address=ip_address(TEST_HOST),
                ip_addresses=[ip_address(TEST_HOST)],
                hostname="mock_hostname",
                name=f"{TEST_NAME}.{type_in_discovery_info}",
                port=None,
                properties={ATTR_PROPERTIES_ID: TEST_DEVICE_ID},
                type=type_in_discovery_info,
            ),
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")

    context = next(
        flow["context"]
        for flow in hass.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    expect(context["title_placeholders"]).to_equal({"name": TEST_NAME})
    expect(context["unique_id"]).to_equal(TEST_NAME)

    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize",
        side_effect=Unavailable,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def reauth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test Nanoleaf reauth flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_NAME,
        data={CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_OTHER_TOKEN},
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
            return_value=_mock_nanoleaf(),
        ),
        patch(
            "homeassistant.components.nanoleaf.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await entry.start_reauth_flow(hass)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("link")

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")

    expect(entry.data[CONF_HOST]).to_equal(TEST_HOST)
    expect(entry.data[CONF_TOKEN]).to_equal(TEST_TOKEN)


_CONF_ONLY_DEVICE_ID = {TEST_DEVICE_ID: {"token": TEST_TOKEN}}
_CONF_ONLY_HOST = {TEST_HOST: {"token": TEST_TOKEN}}
_CONF_DEVICE_ID_AND_HOST = {
    TEST_DEVICE_ID: {"token": TEST_TOKEN},
    TEST_HOST: {"token": TEST_OTHER_TOKEN},
}
_CONF_DEVICE_ID_PLUS_OTHER_HOST = {
    TEST_DEVICE_ID: {"token": TEST_TOKEN},
    TEST_OTHER_HOST: {"token": TEST_OTHER_TOKEN},
}
_CONF_OTHER_DEVICE_ID_PLUS_HOST = {
    TEST_OTHER_DEVICE_ID: {"token": TEST_OTHER_TOKEN},
    TEST_HOST: {"token": TEST_TOKEN},
}


@test.cases(
    test.case(
        "homekit_hap__only_device_id",
        config_entries.SOURCE_HOMEKIT,
        "_hap._tcp.local",
        _CONF_ONLY_DEVICE_ID,
        True,
    ),
    test.case(
        "homekit_hap__only_host",
        config_entries.SOURCE_HOMEKIT,
        "_hap._tcp.local",
        _CONF_ONLY_HOST,
        True,
    ),
    test.case(
        "homekit_hap__device_id_and_host",
        config_entries.SOURCE_HOMEKIT,
        "_hap._tcp.local",
        _CONF_DEVICE_ID_AND_HOST,
        True,
    ),
    test.case(
        "homekit_hap__device_id_plus_other_host",
        config_entries.SOURCE_HOMEKIT,
        "_hap._tcp.local",
        _CONF_DEVICE_ID_PLUS_OTHER_HOST,
        False,
    ),
    test.case(
        "homekit_hap__other_device_id_plus_host",
        config_entries.SOURCE_HOMEKIT,
        "_hap._tcp.local",
        _CONF_OTHER_DEVICE_ID_PLUS_HOST,
        False,
    ),
    test.case(
        "zeroconf_ms__only_device_id",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafms._tcp.local",
        _CONF_ONLY_DEVICE_ID,
        True,
    ),
    test.case(
        "zeroconf_ms__only_host",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafms._tcp.local",
        _CONF_ONLY_HOST,
        True,
    ),
    test.case(
        "zeroconf_ms__device_id_and_host",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafms._tcp.local",
        _CONF_DEVICE_ID_AND_HOST,
        True,
    ),
    test.case(
        "zeroconf_ms__device_id_plus_other_host",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafms._tcp.local",
        _CONF_DEVICE_ID_PLUS_OTHER_HOST,
        False,
    ),
    test.case(
        "zeroconf_ms__other_device_id_plus_host",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafms._tcp.local",
        _CONF_OTHER_DEVICE_ID_PLUS_HOST,
        False,
    ),
    test.case(
        "zeroconf_api__only_device_id",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafapi._tcp.local",
        _CONF_ONLY_DEVICE_ID,
        True,
    ),
    test.case(
        "zeroconf_api__only_host",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafapi._tcp.local",
        _CONF_ONLY_HOST,
        True,
    ),
    test.case(
        "zeroconf_api__device_id_and_host",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafapi._tcp.local",
        _CONF_DEVICE_ID_AND_HOST,
        True,
    ),
    test.case(
        "zeroconf_api__device_id_plus_other_host",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafapi._tcp.local",
        _CONF_DEVICE_ID_PLUS_OTHER_HOST,
        False,
    ),
    test.case(
        "zeroconf_api__other_device_id_plus_host",
        config_entries.SOURCE_ZEROCONF,
        "_nanoleafapi._tcp.local",
        _CONF_OTHER_DEVICE_ID_PLUS_HOST,
        False,
    ),
)
async def import_discovery_integration(
    source: str,
    type_in_discovery: str,
    nanoleaf_conf_file: dict[str, dict[str, str]],
    remove_config: bool,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery integration import."""
    with (
        patch(
            "homeassistant.components.nanoleaf.config_flow.load_json_object",
            return_value=dict(nanoleaf_conf_file),
        ),
        patch(
            "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
            return_value=_mock_nanoleaf(TEST_HOST, TEST_TOKEN),
        ),
        patch(
            "homeassistant.components.nanoleaf.config_flow.save_json",
            return_value=None,
        ) as mock_save_json,
        patch(
            "homeassistant.components.nanoleaf.config_flow.os.remove",
            return_value=None,
        ) as mock_remove,
        patch(
            "homeassistant.components.nanoleaf.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=ZeroconfServiceInfo(
                ip_address=ip_address(TEST_HOST),
                ip_addresses=[ip_address(TEST_HOST)],
                hostname="mock_hostname",
                name=f"{TEST_NAME}.{type_in_discovery}",
                port=None,
                properties={ATTR_PROPERTIES_ID: TEST_DEVICE_ID},
                type=type_in_discovery,
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal({CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN})

    if remove_config:
        mock_save_json.assert_not_called()
        mock_remove.assert_called_once()
    else:
        mock_save_json.assert_called_once()
        mock_remove.assert_not_called()

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def ssdp_discovery(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test SSDP discovery."""
    with (
        patch(
            "homeassistant.components.nanoleaf.config_flow.load_json_object",
            return_value={},
        ),
        patch(
            "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
            return_value=_mock_nanoleaf(TEST_HOST, TEST_TOKEN),
        ),
        patch(
            "homeassistant.components.nanoleaf.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                upnp={},
                ssdp_headers={
                    "_host": TEST_HOST,
                    "nl-devicename": TEST_NAME,
                    "nl-deviceid": TEST_DEVICE_ID,
                },
            ),
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_be(None)
        expect(result["step_id"]).to_equal("link")

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_NAME)
    expect(result2["data"]).to_equal({CONF_HOST: TEST_HOST, CONF_TOKEN: TEST_TOKEN})

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def abort_discovery_flow_with_user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test abort discovery flow if user flow is already in progress."""
    with (
        patch(
            "homeassistant.components.nanoleaf.config_flow.load_json_object",
            return_value={},
        ),
        patch(
            "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
            return_value=_mock_nanoleaf(TEST_HOST, TEST_TOKEN),
        ),
        patch(
            "homeassistant.components.nanoleaf.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                upnp={},
                ssdp_headers={
                    "_host": TEST_HOST,
                    "nl-devicename": TEST_NAME,
                    "nl-deviceid": TEST_DEVICE_ID,
                },
            ),
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_be(None)
        expect(result["step_id"]).to_equal("link")

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        expect(len(hass.config_entries.flow.async_progress(DOMAIN))).to_equal(2)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: TEST_HOST}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("link")

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

        expect(hass.config_entries.flow.async_progress(DOMAIN)).to_be_falsy()
