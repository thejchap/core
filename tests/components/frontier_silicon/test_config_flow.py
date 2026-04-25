"""Test the Frontier Silicon config flow."""

from unittest.mock import AsyncMock, patch

from afsapi import FSConnectionError, FSNotImplementedError, InvalidPinError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.frontier_silicon.const import (
    CONF_WEBFSAPI_URL,
    DEFAULT_PIN,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PIN, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from ._fixtures import (
    config_entry,
    mock_radio_id,
    mock_setup_entry,
    mock_valid_device_url,
    mock_valid_pin,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _device_url: None = Depends(mock_valid_device_url),
    _pin: None = Depends(mock_valid_pin),
    _radio_id: None = Depends(mock_radio_id),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


MOCK_DISCOVERY = SsdpServiceInfo(
    ssdp_usn="mock_usn",
    ssdp_udn="uuid:3dcc7100-f76c-11dd-87af-00226124ca30",
    ssdp_st="mock_st",
    ssdp_location="http://1.1.1.1/device",
    ssdp_headers={"SPEAKER-NAME": "Speaker Name"},
    upnp={"SPEAKER-NAME": "Speaker Name"},
)

INVALID_MOCK_DISCOVERY = SsdpServiceInfo(
    ssdp_usn="mock_usn",
    ssdp_udn="uuid:3dcc7100-f76c-11dd-87af-00226124ca30",
    ssdp_st="mock_st",
    ssdp_location=None,
    ssdp_headers={"SPEAKER-NAME": "Speaker Name"},
    upnp={"SPEAKER-NAME": "Speaker Name"},
)


@test.cases(
    test.case("with_id", radio_id_return_value="mock_radio_id", radio_id_side_effect=None),
    test.case(
        "no_id", radio_id_return_value=None, radio_id_side_effect=FSNotImplementedError
    ),
)
async def form_default_pin(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    radio_id_return_value: str | None,
    radio_id_side_effect,
) -> None:
    """Test manual device add with default pin."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_radio_id",
        return_value=radio_id_return_value,
        side_effect=radio_id_side_effect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 80},
        )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Name of the device")
    expect(result2["data"]).to_equal(
        {
            CONF_WEBFSAPI_URL: "http://1.1.1.1:80/webfsapi",
            CONF_PIN: "1234",
        }
    )
    setup_entry.assert_called_once()


@test.cases(
    test.case("with_id", radio_id_return_value="mock_radio_id", radio_id_side_effect=None),
    test.case(
        "no_id", radio_id_return_value=None, radio_id_side_effect=FSNotImplementedError
    ),
)
async def form_nondefault_pin(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    radio_id_return_value: str | None,
    radio_id_side_effect,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_friendly_name",
        side_effect=InvalidPinError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 80},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("device_config")
    expect(result2["errors"]).to_be(None)

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_radio_id",
        return_value=radio_id_return_value,
        side_effect=radio_id_side_effect,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_PIN: "4321"},
        )
    await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("Name of the device")
    expect(result3["data"]).to_equal(
        {
            CONF_WEBFSAPI_URL: "http://1.1.1.1:80/webfsapi",
            CONF_PIN: "4321",
        }
    )
    setup_entry.assert_called_once()


@test.cases(
    test.case(
        "cannot_connect", friendly_name_error=FSConnectionError, result_error="cannot_connect"
    ),
    test.case("invalid_auth", friendly_name_error=InvalidPinError, result_error="invalid_auth"),
    test.case("unknown", friendly_name_error=ValueError, result_error="unknown"),
)
async def form_nondefault_pin_invalid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    friendly_name_error,
    result_error: str,
) -> None:
    """Test we get the proper errors when trying to validate an user-provided PIN."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_friendly_name",
        side_effect=InvalidPinError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 80},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("device_config")
    expect(result2["errors"]).to_be(None)

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_friendly_name",
        side_effect=friendly_name_error,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_PIN: "4321"},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("device_config")
    expect(result3["errors"]).to_equal({"base": result_error})

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {CONF_PIN: "4321"},
    )
    await hass.async_block_till_done()

    expect(result4["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result4["title"]).to_equal("Name of the device")
    expect(result4["data"]).to_equal(
        {
            CONF_WEBFSAPI_URL: "http://1.1.1.1:80/webfsapi",
            CONF_PIN: "4321",
        }
    )
    setup_entry.assert_called_once()


@test.cases(
    test.case(
        "cannot_connect",
        webfsapi_endpoint_error=FSConnectionError,
        result_error="cannot_connect",
    ),
    test.case("unknown", webfsapi_endpoint_error=ValueError, result_error="unknown"),
)
async def invalid_device_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    webfsapi_endpoint_error,
    result_error: str,
) -> None:
    """Test flow when the user provides an invalid device IP/hostname."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_webfsapi_endpoint",
        side_effect=webfsapi_endpoint_error,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 80},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": result_error})

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {CONF_HOST: "1.1.1.1", CONF_PORT: 80},
    )
    await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("Name of the device")
    expect(result3["data"]).to_equal(
        {
            CONF_WEBFSAPI_URL: "http://1.1.1.1:80/webfsapi",
            CONF_PIN: "1234",
        }
    )
    setup_entry.assert_called_once()


@test.cases(
    test.case("with_id", radio_id_return_value="mock_radio_id", radio_id_side_effect=None),
    test.case(
        "no_id", radio_id_return_value=None, radio_id_side_effect=FSNotImplementedError
    ),
)
async def ssdp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    radio_id_return_value: str | None,
    radio_id_side_effect,
) -> None:
    """Test a device being discovered."""
    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_radio_id",
        return_value=radio_id_return_value,
        side_effect=radio_id_side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_DISCOVERY,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    flow = flows[0]
    expect(flow["context"]["title_placeholders"]).to_equal({"name": "Speaker Name"})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Name of the device")
    expect(result2["data"]).to_equal(
        {
            CONF_WEBFSAPI_URL: "http://1.1.1.1:80/webfsapi",
            CONF_PIN: DEFAULT_PIN,
        }
    )
    setup_entry.assert_called_once()


@test
async def ssdp_invalid_location(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a device being discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=INVALID_MOCK_DISCOVERY,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def ssdp_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test an already known device being discovered."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=MOCK_DISCOVERY,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("unknown", webfsapi_endpoint_error=ValueError, result_error="unknown"),
    test.case(
        "cannot_connect",
        webfsapi_endpoint_error=FSConnectionError,
        result_error="cannot_connect",
    ),
)
async def ssdp_fail(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    webfsapi_endpoint_error,
    result_error: str,
) -> None:
    """Test a device being discovered but failing to reply."""
    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_webfsapi_endpoint",
        side_effect=webfsapi_endpoint_error,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_DISCOVERY,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(result_error)


@test
async def ssdp_nondefault_pin(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a device being discovered."""
    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_friendly_name",
        side_effect=InvalidPinError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_DISCOVERY,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_auth")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test reauth flow."""
    entry.add_to_hass(hass)
    expect(entry.data[CONF_PIN]).to_equal("1234")

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("device_config")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PIN: "4242"},
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_PIN]).to_equal("4242")


@test.cases(
    test.case(
        "cannot_connect", exception=FSConnectionError, reason="cannot_connect"
    ),
    test.case("invalid_auth", exception=InvalidPinError, reason="invalid_auth"),
    test.case("unknown", exception=ValueError, reason="unknown"),
)
async def reauth_flow_friendly_name_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    *,
    exception,
    reason: str,
) -> None:
    """Test reauth flow with failures."""
    entry.add_to_hass(hass)
    expect(entry.data[CONF_PIN]).to_equal("1234")

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("device_config")

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_friendly_name",
        side_effect=exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PIN: "4321"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("device_config")
    expect(result2["errors"]).to_equal({"base": reason})

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PIN: "4242"},
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_PIN]).to_equal("4242")
