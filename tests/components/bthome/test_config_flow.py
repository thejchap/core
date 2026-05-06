"""Test the BTHome config flow."""

from unittest.mock import patch

from bthome_ble import BTHomeBluetoothDeviceData as DeviceData
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothChange
from homeassistant.components.bthome.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    NOT_BTHOME_SERVICE_INFO,
    PRST_SERVICE_INFO,
    TEMP_HUMI_ENCRYPTED_SERVICE_INFO,
    TEMP_HUMI_SERVICE_INFO,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def async_step_bluetooth_valid_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TEMP_HUMI_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("ATC 18B2")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("A4:C1:38:8D:18:B2")


@test
async def async_step_bluetooth_during_onboarding(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth during onboarding."""
    with (
        patch(
            "homeassistant.components.bthome.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.onboarding.async_is_onboarded",
            return_value=False,
        ) as mock_onboarding,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=TEMP_HUMI_SERVICE_INFO,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("ATC 18B2")
    expect(result["data"]).to_equal({})
    expect(result["result"].unique_id).to_equal("A4:C1:38:8D:18:B2")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_onboarding.mock_calls)).to_equal(1)


@test
async def async_step_bluetooth_valid_device_with_encryption(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device, with encryption."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TEMP_HUMI_ENCRYPTED_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("get_encryption_key")

    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TEST DEVICE 80A5")
    expect(result2["data"]).to_equal({"bindkey": "231d39c1d7cc1ab1aee224cd096db932"})
    expect(result2["result"].unique_id).to_equal("54:48:E6:8F:80:A5")


@test
async def async_step_bluetooth_valid_device_encryption_wrong_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device, encrypted, invalid key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TEMP_HUMI_ENCRYPTED_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("get_encryption_key")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("get_encryption_key")
    expect(result2["errors"]["bindkey"]).to_equal("decryption_failed")

    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TEST DEVICE 80A5")
    expect(result2["data"]).to_equal({"bindkey": "231d39c1d7cc1ab1aee224cd096db932"})
    expect(result2["result"].unique_id).to_equal("54:48:E6:8F:80:A5")


@test
async def async_step_bluetooth_valid_device_encryption_wrong_key_length(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device, encrypted, wrong key length."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=TEMP_HUMI_ENCRYPTED_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("get_encryption_key")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "aa"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("get_encryption_key")
    expect(result2["errors"]["bindkey"]).to_equal("expected_32_characters")

    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TEST DEVICE 80A5")
    expect(result2["data"]).to_equal({"bindkey": "231d39c1d7cc1ab1aee224cd096db932"})
    expect(result2["result"].unique_id).to_equal("54:48:E6:8F:80:A5")


@test
async def async_step_bluetooth_not_supported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth not supported."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=NOT_BTHOME_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_supported")


@test
async def async_step_user_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with no devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def async_step_user_no_devices_found_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with no devices found - non-BTHome device."""
    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[NOT_BTHOME_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_devices_found")


@test
async def async_step_user_with_found_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found."""
    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[PRST_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "54:48:E6:8F:80:A5"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("b-parasite 80A5")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("54:48:E6:8F:80:A5")


@test
async def async_step_user_replaces_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache replaces an ignored entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="54:48:E6:8F:80:A5",
        data={},
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[PRST_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "54:48:E6:8F:80:A5"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("b-parasite 80A5")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("54:48:E6:8F:80:A5")


@test
async def async_step_user_with_found_devices_encryption(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found, with encryption."""
    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[TEMP_HUMI_ENCRYPTED_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result1 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "54:48:E6:8F:80:A5"},
    )
    expect(result1["type"]).to_be(FlowResultType.FORM)
    expect(result1["step_id"]).to_equal("get_encryption_key")

    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
        )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TEST DEVICE 80A5")
    expect(result2["data"]).to_equal({"bindkey": "231d39c1d7cc1ab1aee224cd096db932"})
    expect(result2["result"].unique_id).to_equal("54:48:E6:8F:80:A5")


@test
async def async_step_user_with_found_devices_encryption_wrong_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found, with encryption and wrong key."""
    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[TEMP_HUMI_ENCRYPTED_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result1 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "54:48:E6:8F:80:A5"},
    )
    expect(result1["type"]).to_be(FlowResultType.FORM)
    expect(result1["step_id"]).to_equal("get_encryption_key")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("get_encryption_key")
    expect(result2["errors"]["bindkey"]).to_equal("decryption_failed")

    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
        )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TEST DEVICE 80A5")
    expect(result2["data"]).to_equal({"bindkey": "231d39c1d7cc1ab1aee224cd096db932"})
    expect(result2["result"].unique_id).to_equal("54:48:E6:8F:80:A5")


@test
async def async_step_user_with_found_devices_encryption_wrong_key_length(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with encryption and wrong key length."""
    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[TEMP_HUMI_ENCRYPTED_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result1 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "54:48:E6:8F:80:A5"},
    )
    expect(result1["type"]).to_be(FlowResultType.FORM)
    expect(result1["step_id"]).to_equal("get_encryption_key")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "aa"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("get_encryption_key")
    expect(result2["errors"]["bindkey"]).to_equal("expected_32_characters")

    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
        )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TEST DEVICE 80A5")
    expect(result2["data"]).to_equal({"bindkey": "231d39c1d7cc1ab1aee224cd096db932"})
    expect(result2["result"].unique_id).to_equal("54:48:E6:8F:80:A5")


@test
async def async_step_user_device_added_between_steps(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the device gets added via another flow between steps."""
    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[TEMP_HUMI_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="A4:C1:38:8D:18:B2",
    )
    entry.add_to_hass(hass)

    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "A4:C1:38:8D:18:B2"},
        )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def async_step_user_with_found_devices_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="A4:C1:38:8D:18:B2",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[TEMP_HUMI_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def async_step_bluetooth_devices_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow if there is already a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="54:48:E6:8F:80:A5",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRST_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def async_step_bluetooth_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow for the same device twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRST_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRST_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def async_step_user_takes_precedence_over_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=PRST_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[PRST_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "54:48:E6:8F:80:A5"},
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("b-parasite 80A5")
    expect(result2["data"]).to_equal({})
    expect(result2["result"].unique_id).to_equal("54:48:E6:8F:80:A5")

    expect(bool(hass.config_entries.flow.async_progress(DOMAIN))).to_be(False)


@test
async def async_step_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth with a key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="54:48:E6:8F:80:A5",
    )
    entry.add_to_hass(hass)
    saved_callback = None

    def _async_register_callback(_hass, _callback, _matcher, _mode):
        nonlocal saved_callback
        saved_callback = _callback
        return lambda: None

    with patch(
        "homeassistant.components.bluetooth.update_coordinator.async_register_callback",
        _async_register_callback,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)

    saved_callback(TEMP_HUMI_ENCRYPTED_SERVICE_INFO, BluetoothChange.ADVERTISEMENT)
    await hass.async_block_till_done()

    results = hass.config_entries.flow.async_progress()
    expect(len(results)).to_equal(1)
    result = results[0]

    expect(result["step_id"]).to_equal("get_encryption_key")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def async_step_reauth_wrong_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth with a bad key, and that we can recover."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="54:48:E6:8F:80:A5",
    )
    entry.add_to_hass(hass)
    saved_callback = None

    def _async_register_callback(_hass, _callback, _matcher, _mode):
        nonlocal saved_callback
        saved_callback = _callback
        return lambda: None

    with patch(
        "homeassistant.components.bluetooth.update_coordinator.async_register_callback",
        _async_register_callback,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)

    saved_callback(TEMP_HUMI_ENCRYPTED_SERVICE_INFO, BluetoothChange.ADVERTISEMENT)
    await hass.async_block_till_done()

    results = hass.config_entries.flow.async_progress()
    expect(len(results)).to_equal(1)
    result = results[0]

    expect(result["step_id"]).to_equal("get_encryption_key")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "5b51a7c91cde6707c9ef18dada143a58"},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("get_encryption_key")
    expect(result2["errors"]["bindkey"]).to_equal("decryption_failed")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def async_step_reauth_abort_early(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can abort the reauth if there is no encryption."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="54:48:E6:8F:80:A5",
    )
    entry.add_to_hass(hass)

    device = DeviceData()

    result = await entry.start_reauth_flow(hass, data={"device": device})

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
