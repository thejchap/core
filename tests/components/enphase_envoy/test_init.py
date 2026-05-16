"""Test Enphase Envoy runtime."""

from datetime import timedelta
import logging
from unittest.mock import AsyncMock, MagicMock, patch

from freezegun.api import FrozenDateTimeFactory
from jwt import encode
from pyenphase import EnvoyAuthenticationError, EnvoyError, EnvoyTokenAuth
from pyenphase.auth import EnvoyLegacyAuth
from tryke import Depends, expect, fixture, test

from homeassistant.components.enphase_envoy import DOMAIN
from homeassistant.components.enphase_envoy.const import (
    OPTION_DIAGNOSTICS_INCLUDE_FIXTURES,
    OPTION_DISABLE_KEEP_ALIVE,
    Platform,
)
from homeassistant.components.enphase_envoy.coordinator import (
    FIRMWARE_REFRESH_INTERVAL,
    MAC_VERIFICATION_DELAY,
    SCAN_INTERVAL,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ._fixtures import (
    config_entry as config_entry_fixture,
    mock_envoy as mock_envoy_fixture,
    mock_envoy_metered_batt_relay as mock_envoy_metered_batt_relay_fixture,
    setup_integration,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Trigger fixture executor for the module."""
    return 0


@test
async def with_pre_v7_firmware(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test enphase_envoy coordinator with pre V7 firmware."""
    mock_envoy.firmware = "5.1.1"
    mock_envoy.auth = EnvoyLegacyAuth(
        "127.0.0.1", username="test-username", password="test-password"
    )
    await setup_integration(hass, config_entry)

    entity_state = hass.states.get("sensor.inverter_1")
    expect(entity_state).to_be_truthy()
    expect(entity_state.state).to_equal("116")


@test
async def token_in_config_file(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test coordinator with token provided from config."""
    freezer.move_to("2024-07-23 00:00:00+00:00")
    token = encode(
        payload={"name": "envoy", "exp": 1907837780},
        key="secret",
        algorithm="HS256",
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="45a36e55aaddb2007c5f6602e0c38e72",
        title="Envoy 1234",
        unique_id="1234",
        data={
            CONF_HOST: "1.1.1.1",
            CONF_NAME: "Envoy 1234",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_TOKEN: token,
        },
    )
    mock_envoy.auth = EnvoyTokenAuth("127.0.0.1", token=token, envoy_serial="1234")
    await setup_integration(hass, entry)

    entity_state = hass.states.get("sensor.inverter_1")
    expect(entity_state).to_be_truthy()
    expect(entity_state.state).to_equal("116")


@test
async def expired_token_in_config(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test coordinator with expired token provided from config."""
    import respx  # noqa: PLC0415

    freezer.move_to("2024-07-23 00:00:00+00:00")
    current_token = encode(
        payload={"name": "envoy", "exp": 1627314600},
        key="secret",
        algorithm="HS256",
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="45a36e55aaddb2007c5f6602e0c38e72",
        title="Envoy 1234",
        unique_id="1234",
        data={
            CONF_HOST: "1.1.1.1",
            CONF_NAME: "Envoy 1234",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_TOKEN: current_token,
        },
    )
    mock_envoy.auth = EnvoyTokenAuth(
        "127.0.0.1",
        token=current_token,
        envoy_serial="1234",
        cloud_username="test_username",
        cloud_password="test_password",
    )
    with respx.mock:
        await setup_integration(hass, entry)

    entity_state = hass.states.get("sensor.inverter_1")
    expect(entity_state).to_be_truthy()
    expect(entity_state.state).to_equal("116")


@test
async def coordinator_update_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test coordinator update error handling."""
    await setup_integration(hass, config_entry)

    entity_state = hass.states.get("sensor.inverter_1")
    expect(entity_state).to_be_truthy()
    original_state = entity_state

    mock_envoy.data.raw = {"I": "am changed 1"}
    mock_envoy.update.side_effect = EnvoyError

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("sensor.inverter_1")
    expect(entity_state).to_be_truthy()
    expect(entity_state.state).to_equal(STATE_UNAVAILABLE)

    mock_envoy.reset_mock(return_value=True, side_effect=True)

    mock_envoy.data.raw = {"I": "am changed 2"}

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("sensor.inverter_1")
    expect(entity_state).to_be_truthy()
    expect(entity_state.state).to_equal(original_state.state)


@test
async def coordinator_update_authentication_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test enphase_envoy coordinator update authentication error handling."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    mock_envoy.data.raw = {"I": "am changed 1"}
    mock_envoy.update.side_effect = EnvoyAuthenticationError("This must fail")

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_state = hass.states.get("sensor.inverter_1")
    expect(entity_state).to_be_truthy()
    expect(entity_state.state).to_equal(STATE_UNAVAILABLE)


@test
async def coordinator_token_refresh_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test coordinator with expired token and failure to refresh."""
    freezer.move_to("2024-07-23 00:00:00+00:00")
    token = encode(
        payload={"name": "envoy", "exp": 1627314600},
        key="secret",
        algorithm="HS256",
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="45a36e55aaddb2007c5f6602e0c38e72",
        title="Envoy 1234",
        unique_id="1234",
        data={
            CONF_HOST: "1.1.1.1",
            CONF_NAME: "Envoy 1234",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_TOKEN: token,
        },
    )
    mock_envoy.auth = EnvoyTokenAuth("127.0.0.1", token=token, envoy_serial="1234")
    with patch(
        "pyenphase.auth.EnvoyTokenAuth._obtain_token",
        side_effect=EnvoyError,
    ):
        await setup_integration(hass, entry)

    entity_state = hass.states.get("sensor.inverter_1")
    expect(entity_state).to_be_truthy()
    expect(entity_state.state).to_equal("116")


@test
async def coordinator_first_update_auth_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test coordinator update error handling."""
    import respx  # noqa: PLC0415

    freezer.move_to("2024-07-23 00:00:00+00:00")
    current_token = encode(
        payload={"name": "envoy", "exp": 1927314600},
        key="secret",
        algorithm="HS256",
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="45a36e55aaddb2007c5f6602e0c38e72",
        title="Envoy 1234",
        unique_id="1234",
        data={
            CONF_HOST: "1.1.1.1",
            CONF_NAME: "Envoy 1234",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_TOKEN: current_token,
        },
    )
    mock_envoy.auth = EnvoyTokenAuth(
        "127.0.0.1",
        token=current_token,
        envoy_serial="1234",
        cloud_username="test_username",
        cloud_password="test_password",
    )
    mock_envoy.authenticate.side_effect = EnvoyAuthenticationError("Failing test")
    with respx.mock:
        await setup_integration(hass, entry, ConfigEntryState.SETUP_ERROR)


@test
async def config_no_unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
) -> None:
    """Test enphase_envoy init if config entry has no unique id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="45a36e55aaddb2007c5f6602e0c38e72",
        title="Envoy 1234",
        unique_id=None,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_NAME: "Envoy 1234",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    await setup_integration(hass, entry)
    expect(entry.unique_id).to_equal(mock_envoy.serial_number)


@test
async def config_different_unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
) -> None:
    """Test enphase_envoy init if config entry has different unique id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="45a36e55aaddb2007c5f6602e0c38e72",
        title="Envoy 1234",
        unique_id="4321",
        data={
            CONF_HOST: "1.1.1.1",
            CONF_NAME: "Envoy 1234",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    await setup_integration(hass, entry, expected_state=ConfigEntryState.SETUP_RETRY)


@test.skip("hass_ws_client requires further fixture wiring for tryke port")
async def remove_config_entry_device() -> None:
    """Stub for test_remove_config_entry_device (port deferred)."""


@test
async def option_change_reload(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
) -> None:
    """Test options change will reload entity."""
    await setup_integration(hass, config_entry)
    expect(config_entry.options).to_equal({})

    hass.config_entries.async_update_entry(
        config_entry,
        options={
            OPTION_DIAGNOSTICS_INCLUDE_FIXTURES: False,
            OPTION_DISABLE_KEEP_ALIVE: True,
        },
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.options).to_equal(
        {
            OPTION_DIAGNOSTICS_INCLUDE_FIXTURES: False,
            OPTION_DISABLE_KEEP_ALIVE: True,
        }
    )
    hass.config_entries.async_update_entry(
        config_entry,
        options={
            OPTION_DIAGNOSTICS_INCLUDE_FIXTURES: True,
            OPTION_DISABLE_KEEP_ALIVE: False,
        },
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.options).to_equal(
        {
            OPTION_DIAGNOSTICS_INCLUDE_FIXTURES: True,
            OPTION_DISABLE_KEEP_ALIVE: False,
        }
    )


def _mock_envoy_setup(mock_envoy: AsyncMock) -> None:
    """Mock envoy.setup."""
    mock_envoy.firmware = "9.9.9999"


@test
async def coordinator_firmware_refresh(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test coordinator scheduled firmware check."""
    import respx  # noqa: PLC0415

    with (
        patch(
            "homeassistant.components.enphase_envoy.coordinator.SCAN_INTERVAL",
            timedelta(days=1),
        ),
        respx.mock,
    ):
        await setup_integration(hass, config_entry)

        mock_envoy.setup.reset_mock()
        freezer.tick(FIRMWARE_REFRESH_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

        mock_envoy.setup.assert_called_once_with()
        mock_envoy.setup.reset_mock()

        envoy = config_entry.runtime_data.envoy
        expect(envoy.firmware).to_equal("7.6.175")

        caplog.set_level(logging.WARNING)

        with patch(
            "homeassistant.components.enphase_envoy.Envoy.setup",
            MagicMock(return_value=_mock_envoy_setup(mock_envoy)),
        ):
            freezer.tick(FIRMWARE_REFRESH_INTERVAL)
            async_fire_time_changed(hass)
            await hass.async_block_till_done(wait_background_tasks=True)

            expect(
                "Envoy firmware changed from: 7.6.175 to: 9.9.9999, reloading config entry Envoy 1234"
                in caplog.text
            ).to_be_truthy()
            envoy = config_entry.runtime_data.envoy
            expect(envoy.firmware).to_equal("9.9.9999")


@test
async def coordinator_firmware_refresh_with_envoy_error(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test coordinator scheduled firmware check."""
    import respx  # noqa: PLC0415

    with respx.mock:
        await setup_integration(hass, config_entry)

        caplog.set_level(logging.DEBUG)
        logging.getLogger(
            "homeassistant.components.enphase_envoy.coordinator"
        ).setLevel(logging.DEBUG)

        mock_envoy.setup.side_effect = EnvoyError
        freezer.tick(FIRMWARE_REFRESH_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

        expect("Error reading firmware:" in caplog.text).to_be_truthy()


@test
async def coordinator_interface_information(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test coordinator interface mac verification."""
    import respx  # noqa: PLC0415

    with respx.mock:
        await setup_integration(hass, config_entry)

        caplog.set_level(logging.DEBUG)
        logging.getLogger(
            "homeassistant.components.enphase_envoy.coordinator"
        ).setLevel(logging.DEBUG)

        freezer.tick(MAC_VERIFICATION_DELAY)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

        expect("added connection" in caplog.text).to_be_truthy()

        hass.config_entries.async_update_entry(
            config_entry,
            options={
                OPTION_DIAGNOSTICS_INCLUDE_FIXTURES: False,
                OPTION_DISABLE_KEEP_ALIVE: True,
            },
        )
        await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)

        caplog.clear()
        freezer.tick(MAC_VERIFICATION_DELAY)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

        expect("connection verified as existing" in caplog.text).to_be_truthy()


@test
async def coordinator_interface_information_no_device(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test coordinator interface mac verification full code cov."""
    import respx  # noqa: PLC0415

    with respx.mock:
        await setup_integration(hass, config_entry)

        caplog.set_level(logging.DEBUG)
        logging.getLogger(
            "homeassistant.components.enphase_envoy.coordinator"
        ).setLevel(logging.DEBUG)

        envoy_device = device_registry.async_get_device(
            identifiers={
                (
                    DOMAIN,
                    mock_envoy.serial_number,
                )
            }
        )
        device_registry.async_update_device(
            device_id=envoy_device.id,
            new_identifiers={(DOMAIN, "9999")},
        )

        freezer.tick(MAC_VERIFICATION_DELAY)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

        expect(
            "No envoy device found in device registry" in caplog.text
        ).to_be_truthy()


@test
async def coordinator_interface_information_mac_also_in_other_device(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    mock_envoy: AsyncMock = Depends(mock_envoy_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test coordinator interface mac verification with MAC also in other existing device."""
    import respx  # noqa: PLC0415

    with respx.mock:
        await setup_integration(hass, config_entry)

        caplog.set_level(logging.DEBUG)
        logging.getLogger(
            "homeassistant.components.enphase_envoy.coordinator"
        ).setLevel(logging.DEBUG)

        other_config_entry = MockConfigEntry(domain="test", data={})
        other_config_entry.add_to_hass(hass)
        device_registry.async_get_or_create(
            config_entry_id=other_config_entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, "00:11:22:33:44:55")},
            manufacturer="Enphase Energy",
        )

        envoy_device = device_registry.async_get_device(
            identifiers={
                (
                    DOMAIN,
                    mock_envoy.serial_number,
                )
            }
        )
        expect(envoy_device).to_be_truthy()

        freezer.tick(MAC_VERIFICATION_DELAY)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

        expect(
            "added connection: ('mac', '00:11:22:33:44:55') to Envoy 1234"
            in caplog.text
        ).to_be_truthy()

        envoy_device_refetched = device_registry.async_get(envoy_device.id)
        expect(envoy_device_refetched).to_be_truthy()
        expect(envoy_device_refetched.name).to_equal("Envoy 1234")
        expect(envoy_device_refetched.serial_number).to_equal("1234")
        expect(envoy_device_refetched.connections).to_equal(
            {
                (
                    dr.CONNECTION_NETWORK_MAC,
                    "00:11:22:33:44:55",
                )
            }
        )


