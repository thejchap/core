"""Define tests for the Nettigo Air Monitor config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

from nettigo_air_monitor import ApiError, AuthFailedError, CannotGetMacError
from tryke import Depends, expect, fixture, test

from homeassistant.components.nam.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_async_zeroconf, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address("10.10.2.3"),
    ip_addresses=[ip_address("10.10.2.3")],
    hostname="mock_hostname",
    name="mock_name",
    port=None,
    properties={},
    type="mock_type",
)
VALID_CONFIG = {"host": "10.10.2.3"}
VALID_AUTH = {"username": "fake_username", "password": "fake_password"}


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _maz: MagicMock = Depends(mock_async_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form_create_entry_without_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user step without auth works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.10.2.3")
    expect(result["data"]["host"]).to_equal("10.10.2.3")
    expect(len(mse.mock_calls)).to_equal(1)


@test
async def form_create_entry_with_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user step with auth works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=[AuthFailedError("Authorization has failed"), "aa:bb:cc:dd:ee:ff"],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("credentials")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_AUTH,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.10.2.3")
    expect(result["data"]["host"]).to_equal("10.10.2.3")
    expect(result["data"]["username"]).to_equal("fake_username")
    expect(result["data"]["password"]).to_equal("fake_password")
    expect(len(mse.mock_calls)).to_equal(1)


@test
async def reauth_successful(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test starting a reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="10.10.2.3",
        unique_id="aa:bb:cc:dd:ee:ff",
        data={"host": "10.10.2.3"},
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_AUTH,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_unsuccessful(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test starting a reauthentication flow that fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="10.10.2.3",
        unique_id="aa:bb:cc:dd:ee:ff",
        data={"host": "10.10.2.3"},
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=ApiError("API Error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_AUTH,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_unsuccessful")


@test.cases(
    test.case("api_error", ApiError("API Error"), "cannot_connect"),
    test.case("auth_failed", AuthFailedError("Auth Error"), "invalid_auth"),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("value_error", ValueError, "unknown"),
)
async def form_with_auth_errors(
    exc: type[Exception] | Exception,
    base_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle errors when auth is required."""
    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=AuthFailedError("Authorization has failed"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=VALID_CONFIG,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("credentials")

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=exc,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_AUTH,
        )

    expect(result["errors"]).to_equal({"base": base_error})


@test.cases(
    test.case("api_error", ApiError("API Error"), "cannot_connect"),
    test.case("timeout", TimeoutError, "cannot_connect"),
    test.case("value_error", ValueError, "unknown"),
)
async def form_errors(
    exc: type[Exception] | Exception,
    base_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle errors."""
    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.initialize",
        side_effect=exc,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=VALID_CONFIG,
        )

    expect(result["errors"]).to_equal({"base": base_error})


@test
async def form_abort(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle abort after error."""
    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=CannotGetMacError("Cannot get MAC address from device"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=VALID_CONFIG,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("device_unsupported")


@test
async def form_already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that errors are shown when duplicates are added."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="aa:bb:cc:dd:ee:ff", data=VALID_CONFIG
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data["host"]).to_equal("1.1.1.1")


@test
async def zeroconf(
    hass: HomeAssistant = Depends(hass_fixture),
    mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the zeroconf flow."""
    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": SOURCE_ZEROCONF},
        )
        context = next(
            flow["context"]
            for flow in hass.config_entries.flow.async_progress()
            if flow["flow_id"] == result["flow_id"]
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(context["title_placeholders"]["host"]).to_equal("10.10.2.3")
    expect(context["confirm_only"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.10.2.3")
    expect(result["data"]).to_equal({"host": "10.10.2.3"})
    expect(len(mse.mock_calls)).to_equal(1)


@test
async def zeroconf_with_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the zeroconf step with auth works."""
    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=AuthFailedError("Auth Error"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": SOURCE_ZEROCONF},
        )
        context = next(
            flow["context"]
            for flow in hass.config_entries.flow.async_progress()
            if flow["flow_id"] == result["flow_id"]
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("credentials")
    expect(result["errors"]).to_equal({})
    expect(context["title_placeholders"]["host"]).to_equal("10.10.2.3")

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_AUTH,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.10.2.3")
    expect(result["data"]["host"]).to_equal("10.10.2.3")
    expect(result["data"]["username"]).to_equal("fake_username")
    expect(result["data"]["password"]).to_equal("fake_password")
    expect(len(mse.mock_calls)).to_equal(1)


@test
async def zeroconf_host_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that errors are shown when host is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="aa:bb:cc:dd:ee:ff", data=VALID_CONFIG
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=DISCOVERY_INFO,
        context={"source": SOURCE_ZEROCONF},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("api_error", ApiError("API Error"), "cannot_connect"),
    test.case(
        "cannot_get_mac",
        CannotGetMacError("Cannot get MAC address from device"),
        "device_unsupported",
    ),
)
async def zeroconf_errors(
    exc: Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle errors."""
    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.initialize",
        side_effect=exc,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": SOURCE_ZEROCONF},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def reconfigure_successful(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test starting a reconfigure flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="10.10.2.3",
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_HOST: "10.10.2.3",
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "10.10.10.10"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            CONF_HOST: "10.10.10.10",
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        }
    )


@test
async def reconfigure_not_successful(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test starting a reconfigure flow but no connection found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="10.10.2.3",
        unique_id="aa:bb:cc:dd:ee:ff",
        data={
            CONF_HOST: "10.10.2.3",
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=ApiError("API Error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "10.10.10.10"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "10.10.10.10"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            CONF_HOST: "10.10.10.10",
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        }
    )


@test
async def reconfigure_not_the_same_device(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting the reconfiguration process, but with a different printer."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="10.10.2.3",
        unique_id="11:22:33:44:55:66",
        data={
            CONF_HOST: "10.10.2.3",
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "10.10.10.10"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("another_device")
