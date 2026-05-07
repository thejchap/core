"""Configuration flow tests for the Peblar integration."""

from ipaddress import ip_address
from unittest.mock import MagicMock

from peblar import PeblarAuthenticationError, PeblarConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.peblar.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_config_entry, mock_peblar, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Anchor fixture (mock_setup_entry autouse equivalent)."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
) -> None:
    """Test the full happy path user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGPUPPIES"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("23-45-A4O-MOF")
    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGPUPPIES"}
    )
    expect(not config_entry.options).to_be(True)


@test.cases(
    test.case("connection_error", side_effect=PeblarConnectionError, expected_error={CONF_HOST: "cannot_connect"}),
    test.case("auth_error", side_effect=PeblarAuthenticationError, expected_error={CONF_PASSWORD: "invalid_auth"}),
    test.case("unknown", side_effect=Exception, expected_error={"base": "unknown"}),
)
async def user_flow_errors(
    side_effect: type[Exception],
    expected_error: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
) -> None:
    """Test we show user form on a connection error."""
    peblar.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGCATS!"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal(expected_error)

    peblar.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.2", CONF_PASSWORD: "OMGPUPPIES!"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("23-45-A4O-MOF")
    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.2", CONF_PASSWORD: "OMGPUPPIES!"}
    )
    expect(not config_entry.options).to_be(True)


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test configuration flow aborts when the device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGSPIDERS"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the full happy path reconfigure flow from start to finish."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.127", CONF_PASSWORD: "OMGSPIDERS"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGPUPPIES"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGPUPPIES"}
    )


@test
async def reconfigure_to_different_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguring to a different device doesn't work."""
    config_entry.add_to_hass(hass)

    hass.config_entries.async_update_entry(config_entry, unique_id="mismatch")

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGPUPPIES"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("different_device")


@test.cases(
    test.case("connection_error", side_effect=PeblarConnectionError, expected_error={CONF_HOST: "cannot_connect"}),
    test.case("auth_error", side_effect=PeblarAuthenticationError, expected_error={CONF_PASSWORD: "invalid_auth"}),
    test.case("unknown", side_effect=Exception, expected_error={"base": "unknown"}),
)
async def reconfigure_flow_errors(
    side_effect: type[Exception],
    expected_error: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we show user form on a connection error."""
    config_entry.add_to_hass(hass)
    peblar.login.side_effect = side_effect

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGPUPPIES"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(expected_error)

    peblar.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.2", CONF_PASSWORD: "OMGPUPPIES"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)

    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.2", CONF_PASSWORD: "OMGPUPPIES"}
    )


@test
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
) -> None:
    """Test the zeroconf happy flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="pblr-0000645.local.",
            name="mock_name",
            properties={"sn": "23-45-A4O-MOF", "version": "1.6.1+1+WL-1"},
            type="mock_type",
        ),
    )

    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    progress = hass.config_entries.flow.async_progress()
    expect(len(progress)).to_equal(1)
    expect(progress[0].get("flow_id")).to_equal(result["flow_id"])

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "OMGPINEAPPLES"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("23-45-A4O-MOF")
    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGPINEAPPLES"}
    )
    expect(not config_entry.options).to_be(True)


@test
async def zeroconf_flow_abort_no_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the zeroconf aborts when it advertises incompatible data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="pblr-0000645.local.",
            name="mock_name",
            properties={},
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_serial_number")


@test.cases(
    test.case("connection_error", side_effect=PeblarConnectionError, expected_error={"base": "cannot_connect"}),
    test.case("auth_error", side_effect=PeblarAuthenticationError, expected_error={CONF_PASSWORD: "invalid_auth"}),
    test.case("unknown", side_effect=Exception, expected_error={"base": "unknown"}),
)
async def zeroconf_flow_errors(
    side_effect: type[Exception],
    expected_error: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
) -> None:
    """Test we show form on a error."""
    peblar.login.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="pblr-0000645.local.",
            name="mock_name",
            properties={"sn": "23-45-A4O-MOF", "version": "1.6.1+1+WL-1"},
            type="mock_type",
        ),
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "OMGPUPPIES"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["errors"]).to_equal(expected_error)

    peblar.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "OMGPUPPIES"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("23-45-A4O-MOF")
    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGPUPPIES"}
    )
    expect(not config_entry.options).to_be(True)


@test
async def zeroconf_flow_not_discovered_again(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the zeroconf doesn't re-discover an existing device."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="pblr-0000645.local.",
            name="mock_name",
            properties={"sn": "23-45-A4O-MOF", "version": "1.6.1+1+WL-1"},
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_with_zeroconf_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
) -> None:
    """Test user flow while zeroconf discovery is in progress."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="pblr-0000645.local.",
            name="mock_name",
            properties={"sn": "23-45-A4O-MOF", "version": "1.6.1+1+WL-1"},
            type="mock_type",
        ),
    )

    progress = hass.config_entries.flow.async_progress()
    expect(len(progress)).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    progress = hass.config_entries.flow.async_progress()
    expect(len(progress)).to_equal(2)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_PASSWORD: "OMGPUPPIES"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(not hass.config_entries.flow.async_progress()).to_be(True)


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reauthentication configuration flow."""
    config_entry.add_to_hass(hass)
    expect(config_entry.data[CONF_PASSWORD]).to_equal("OMGSPIDERS")

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "OMGPUPPIES"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.127", CONF_PASSWORD: "OMGPUPPIES"}
    )


@test.cases(
    test.case("connection_error", side_effect=PeblarConnectionError, expected_error={"base": "cannot_connect"}),
    test.case("auth_error", side_effect=PeblarAuthenticationError, expected_error={CONF_PASSWORD: "invalid_auth"}),
    test.case("unknown", side_effect=Exception, expected_error={"base": "unknown"}),
)
async def reauth_flow_errors(
    side_effect: type[Exception],
    expected_error: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    peblar: MagicMock = Depends(mock_peblar),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we show form on a error."""
    config_entry.add_to_hass(hass)
    peblar.login.side_effect = side_effect

    result = await config_entry.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "OMGPUPPIES"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal(expected_error)

    peblar.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "OMGPUPPIES"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
