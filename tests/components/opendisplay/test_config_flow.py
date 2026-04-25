"""Test the OpenDisplay config flow."""

from unittest.mock import MagicMock, patch

from opendisplay import (
    AuthenticationFailedError,
    AuthenticationRequiredError,
    BLEConnectionError,
    BLETimeoutError,
    OpenDisplayError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.opendisplay.const import CONF_ENCRYPTION_KEY, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import ENCRYPTION_KEY, NOT_OPENDISPLAY_SERVICE_INFO, VALID_SERVICE_INFO
from ._fixtures import (
    mock_ble_device,
    mock_config_entry,
    mock_encrypted_config_entry,
    mock_opendisplay_device,
    mock_opendisplay_device_class,
    mock_setup_entry,
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
    _ble: None = Depends(mock_ble_device),
    _device: MagicMock = Depends(mock_opendisplay_device),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def bluetooth_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via Bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VALID_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenDisplay 1234")
    expect(result["data"]).to_equal({})
    expect(result["result"].unique_id).to_equal("AA:BB:CC:DD:EE:FF")


@test
async def bluetooth_discovery_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test discovery aborts when device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VALID_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def bluetooth_discovery_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery aborts when same device flow is in progress."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VALID_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VALID_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test.cases(
    test.case(
        "ble_connection",
        exception=BLEConnectionError("test"),
        expected_reason="cannot_connect",
    ),
    test.case(
        "ble_timeout",
        exception=BLETimeoutError("test"),
        expected_reason="cannot_connect",
    ),
    test.case(
        "opendisplay",
        exception=OpenDisplayError("test"),
        expected_reason="cannot_connect",
    ),
    test.case(
        "runtime", exception=RuntimeError("test"), expected_reason="unknown"
    ),
)
async def bluetooth_confirm_connection_error(
    *,
    exception: Exception,
    expected_reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_opendisplay_device),
) -> None:
    """Test confirm step aborts when connection fails before showing the form."""
    device.__aenter__.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VALID_SERVICE_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)


@test
async def bluetooth_confirm_ble_device_not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test confirm step aborts when BLE device is not found."""
    with patch(
        "homeassistant.components.opendisplay.config_flow.async_ble_device_from_address",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=VALID_SERVICE_INFO,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def user_step_with_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with discovered devices."""
    with patch(
        "homeassistant.components.opendisplay.config_flow.async_discovered_service_info",
        return_value=[VALID_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "AA:BB:CC:DD:EE:FF"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("OpenDisplay 1234")
    expect(result["data"]).to_equal({})
    expect(result["result"].unique_id).to_equal("AA:BB:CC:DD:EE:FF")


@test
async def user_step_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step when no devices are discovered."""
    with patch(
        "homeassistant.components.opendisplay.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_step_filters_unsupported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step filters out unsupported devices."""
    with patch(
        "homeassistant.components.opendisplay.config_flow.async_discovered_service_info",
        return_value=[NOT_OPENDISPLAY_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test.cases(
    test.case(
        "ble_connection",
        exception=BLEConnectionError("test"),
        expected_error="cannot_connect",
    ),
    test.case(
        "ble_timeout",
        exception=BLETimeoutError("test"),
        expected_error="cannot_connect",
    ),
    test.case(
        "opendisplay",
        exception=OpenDisplayError("test"),
        expected_error="cannot_connect",
    ),
    test.case(
        "runtime", exception=RuntimeError("test"), expected_error="unknown"
    ),
)
async def user_step_connection_error(
    *,
    exception: Exception,
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_opendisplay_device),
) -> None:
    """Test user step handles connection and unexpected errors."""
    with patch(
        "homeassistant.components.opendisplay.config_flow.async_discovered_service_info",
        return_value=[VALID_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)

    device.__aenter__.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "AA:BB:CC:DD:EE:FF"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    device.__aenter__.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "AA:BB:CC:DD:EE:FF"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_step_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user step aborts when device is already configured."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.opendisplay.config_flow.async_discovered_service_info",
        return_value=[VALID_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def bluetooth_discovery_encrypted_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_opendisplay_device),
) -> None:
    """Test Bluetooth discovery prompts for key when device requires encryption."""
    device.__aenter__.side_effect = [
        AuthenticationRequiredError("auth required"),
        device,
    ]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VALID_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("encryption_key")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: ENCRYPTION_KEY},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ENCRYPTION_KEY: ENCRYPTION_KEY})


@test
async def bluetooth_discovery_encrypted_invalid_key_format(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_opendisplay_device),
) -> None:
    """Test encryption_key step shows error on invalid key format."""
    device.__aenter__.side_effect = [
        AuthenticationRequiredError("auth required"),
        device,
    ]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VALID_SERVICE_INFO,
    )
    expect(result["step_id"]).to_equal("encryption_key")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: "tooshort"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("encryption_key")
    expect(result["errors"]).to_equal({CONF_ENCRYPTION_KEY: "invalid_key_format"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: ENCRYPTION_KEY},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def bluetooth_discovery_encrypted_wrong_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_opendisplay_device),
) -> None:
    """Test encryption_key step shows error on wrong key, then succeeds."""
    device.__aenter__.side_effect = [
        AuthenticationRequiredError("auth required"),
        AuthenticationFailedError("wrong key"),
        device,
    ]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=VALID_SERVICE_INFO,
    )
    expect(result["step_id"]).to_equal("encryption_key")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: ENCRYPTION_KEY},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_ENCRYPTION_KEY: "invalid_auth"})

    device.__aenter__.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: ENCRYPTION_KEY},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ENCRYPTION_KEY: ENCRYPTION_KEY})


@test
async def user_step_encrypted_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_opendisplay_device),
) -> None:
    """Test user step prompts for key when device requires encryption."""
    device.__aenter__.side_effect = [
        AuthenticationRequiredError("auth required"),
        device,
    ]

    with patch(
        "homeassistant.components.opendisplay.config_flow.async_discovered_service_info",
        return_value=[VALID_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "AA:BB:CC:DD:EE:FF"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("encryption_key")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: ENCRYPTION_KEY},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ENCRYPTION_KEY: ENCRYPTION_KEY})


@test
async def reauth_update_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_opendisplay_device),
    encrypted_entry: MockConfigEntry = Depends(mock_encrypted_config_entry),
) -> None:
    """Test reauth flow updates the encryption key."""
    encrypted_entry.add_to_hass(hass)
    new_key = "11223344556677881122334455667788"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": encrypted_entry.entry_id,
        },
        data=encrypted_entry.data,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: new_key},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(encrypted_entry.data[CONF_ENCRYPTION_KEY]).to_equal(new_key)


@test
async def reauth_remove_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_opendisplay_device),
    encrypted_entry: MockConfigEntry = Depends(mock_encrypted_config_entry),
) -> None:
    """Test reauth flow removes the encryption key when left blank."""
    encrypted_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": encrypted_entry.entry_id,
        },
        data=encrypted_entry.data,
    )
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: ""},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(CONF_ENCRYPTION_KEY not in encrypted_entry.data).to_be(True)


@test
async def reauth_wrong_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_opendisplay_device),
    encrypted_entry: MockConfigEntry = Depends(mock_encrypted_config_entry),
) -> None:
    """Test reauth form shows error for wrong key, then succeeds."""
    encrypted_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": encrypted_entry.entry_id,
        },
        data=encrypted_entry.data,
    )
    expect(result["step_id"]).to_equal("reauth_confirm")

    device.__aenter__.side_effect = [
        AuthenticationFailedError("wrong key"),
        device,
    ]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: ENCRYPTION_KEY},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_ENCRYPTION_KEY: "invalid_auth"})

    device.__aenter__.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: ENCRYPTION_KEY},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_invalid_key_format(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    encrypted_entry: MockConfigEntry = Depends(mock_encrypted_config_entry),
) -> None:
    """Test reauth form shows error for a malformed encryption key."""
    encrypted_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": encrypted_entry.entry_id,
        },
        data=encrypted_entry.data,
    )
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENCRYPTION_KEY: "notvalidhex!"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_ENCRYPTION_KEY: "invalid_key_format"})
