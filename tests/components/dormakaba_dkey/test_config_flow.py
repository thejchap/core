"""Test the Dormakaba dKey config flow."""

from unittest.mock import patch

from bleak.exc import BleakError
from py_dormakaba_dkey import errors as dkey_errors
from py_dormakaba_dkey.models import AssociationData
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.dormakaba_dkey.const import DOMAIN
from homeassistant.config_entries import SOURCE_IGNORE
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType

from . import DKEY_DISCOVERY_INFO, NOT_DKEY_DISCOVERY_INFO

from tests.common import MockConfigEntry
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


async def _test_common_success(hass: HomeAssistant, result: FlowResult) -> None:
    """Test bluetooth and user flow success paths."""
    with (
        patch(
            "homeassistant.components.dormakaba_dkey.config_flow.DKEYLock.associate",
            return_value=AssociationData(b"1234", b"AABBCCDD"),
        ) as mock_associate,
        patch(
            "homeassistant.components.dormakaba_dkey.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"activation_code": "1234-1234"}
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DKEY_DISCOVERY_INFO.name)
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: DKEY_DISCOVERY_INFO.address,
            "association_data": {
                "key_holder_id": "31323334",
                "secret": "4141424243434444",
            },
        }
    )
    expect(result["options"]).to_equal({})
    expect(result["result"].unique_id).to_equal(DKEY_DISCOVERY_INFO.address)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    mock_associate.assert_awaited_once_with("1234-1234")


@test
async def user_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step success path."""
    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_discovered_service_info",
        return_value=[NOT_DKEY_DISCOVERY_INFO, DKEY_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADDRESS: DKEY_DISCOVERY_INFO.address},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("associate")
    expect(result["errors"]).to_be(None)

    await _test_common_success(hass, result)


@test
async def user_step_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with no devices found."""
    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_discovered_service_info",
        return_value=[NOT_DKEY_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_step_no_new_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with only existing devices found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_ADDRESS: DKEY_DISCOVERY_INFO.address},
        unique_id=DKEY_DISCOVERY_INFO.address,
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_discovered_service_info",
        return_value=[DKEY_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_step_device_added_between_steps_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the device gets added via another flow between steps."""
    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_discovered_service_info",
        return_value=[DKEY_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DKEY_DISCOVERY_INFO.address,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": DKEY_DISCOVERY_INFO.address},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def async_step_user_takes_precedence_over_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=DKEY_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_discovered_service_info",
        return_value=[DKEY_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADDRESS: DKEY_DISCOVERY_INFO.address},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("associate")
    expect(result["errors"]).to_be(None)

    await _test_common_success(hass, result)

    expect(bool(hass.config_entries.flow.async_progress(DOMAIN))).to_be(False)


@test
async def user_setup_removes_ignored_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form can replace an ignored device."""
    ignored_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DKEY_DISCOVERY_INFO.address,
        source=SOURCE_IGNORE,
    )
    ignored_entry.add_to_hass(hass)
    expect(hass.config_entries.async_entries(DOMAIN)).to_equal([ignored_entry])

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_discovered_service_info",
        return_value=[NOT_DKEY_DISCOVERY_INFO, DKEY_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADDRESS: DKEY_DISCOVERY_INFO.address},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("associate")
    expect(result["errors"]).to_be(None)

    await _test_common_success(hass, result)

    expect(ignored_entry not in hass.config_entries.async_entries(DOMAIN)).to_be(True)


@test
async def bluetooth_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth step success path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=DKEY_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("associate")
    expect(result["errors"]).to_be(None)

    await _test_common_success(hass, result)


@test
async def bluetooth_step_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth step already configured path."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DKEY_DISCOVERY_INFO.address)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=DKEY_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def bluetooth_step_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow for the same device twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=DKEY_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=DKEY_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test.cases(
    test.case("cannot_connect", exc=BleakError, error="cannot_connect"),
    test.case("unknown", exc=Exception, error="unknown"),
)
async def bluetooth_step_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exc: type[Exception],
    error: str,
) -> None:
    """Test bluetooth step and we cannot connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=DKEY_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("associate")
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.DKEYLock.associate",
        side_effect=exc,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"activation_code": "1234-1234"}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error)


@test.cases(
    test.case(
        "invalid_code",
        exc=dkey_errors.InvalidActivationCode,
        error="invalid_code",
    ),
    test.case("wrong_code", exc=dkey_errors.WrongActivationCode, error="wrong_code"),
)
async def bluetooth_step_cannot_associate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exc: type[Exception],
    error: str,
) -> None:
    """Test bluetooth step and we cannot associate."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=DKEY_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("associate")
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.DKEYLock.associate",
        side_effect=exc,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"activation_code": "1234-1234"}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("associate")
    expect(result["errors"]).to_equal({"base": error})


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauthentication."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DKEY_DISCOVERY_INFO.address,
        data={"address": DKEY_DISCOVERY_INFO.address},
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_last_service_info",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "no_longer_in_range"})

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_last_service_info",
        return_value=DKEY_DISCOVERY_INFO,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("associate")
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.dormakaba_dkey.config_flow.DKEYLock.associate",
            return_value=AssociationData(b"1234", b"AABBCCDD"),
        ) as mock_associate,
        patch(
            "homeassistant.components.dormakaba_dkey.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"activation_code": "1234-1234"}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            CONF_ADDRESS: DKEY_DISCOVERY_INFO.address,
            "association_data": {
                "key_holder_id": "31323334",
                "secret": "4141424243434444",
            },
        }
    )
    mock_associate.assert_awaited_once_with("1234-1234")
