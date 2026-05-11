"""Test for airOS integration setup."""

from unittest.mock import ANY, AsyncMock, MagicMock

from airos.exceptions import (
    AirOSConnectionAuthenticationError,
    AirOSConnectionSetupError,
    AirOSDeviceConnectionError,
    AirOSKeyDataMissingError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.airos.const import (
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    SECTION_ADVANCED_SETTINGS,
)
from homeassistant.components.airos.coordinator import async_fetch_airos_data
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import (
    SOURCE_USER,
    ConfigEntryAuthFailed,
    ConfigEntryState,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from ._fixtures import (
    mock_airos_class,
    mock_airos_client,
    mock_async_get_firmware_data,
    mock_config_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import device_registry as device_registry_fixture, hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async

MOCK_CONFIG_V1 = {
    CONF_HOST: "1.1.1.1",
    CONF_USERNAME: "ubnt",
    CONF_PASSWORD: "test-password",
}

MOCK_CONFIG_PLAIN = {
    CONF_HOST: "1.1.1.1",
    CONF_USERNAME: "ubnt",
    CONF_PASSWORD: "test-password",
    SECTION_ADVANCED_SETTINGS: {
        CONF_SSL: False,
        CONF_VERIFY_SSL: False,
    },
}

MOCK_CONFIG_V1_2 = {
    CONF_HOST: "1.1.1.1",
    CONF_USERNAME: "ubnt",
    CONF_PASSWORD: "test-password",
    SECTION_ADVANCED_SETTINGS: {
        CONF_SSL: DEFAULT_SSL,
        CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
    },
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def setup_entry_with_default_ssl(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_airos_class: MagicMock = Depends(mock_airos_class),
    mock_airos_client: MagicMock = Depends(mock_airos_client),
    mock_async_get_firmware_data: AsyncMock = Depends(mock_async_get_firmware_data),
) -> None:
    """Test setting up a config entry with default SSL options."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    mock_airos_class.assert_called_once_with(
        host=mock_config_entry.data[CONF_HOST],
        username=mock_config_entry.data[CONF_USERNAME],
        password=mock_config_entry.data[CONF_PASSWORD],
        session=ANY,
        use_ssl=DEFAULT_SSL,
    )

    expect(mock_config_entry.data[SECTION_ADVANCED_SETTINGS][CONF_SSL]).to_be(True)
    expect(mock_config_entry.data[SECTION_ADVANCED_SETTINGS][CONF_VERIFY_SSL]).to_be(
        False
    )


@test
async def setup_entry_without_ssl(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airos_class: MagicMock = Depends(mock_airos_class),
    mock_airos_client: MagicMock = Depends(mock_airos_client),
    mock_async_get_firmware_data: AsyncMock = Depends(mock_async_get_firmware_data),
) -> None:
    """Test setting up a config entry adjusted to plain HTTP."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_PLAIN,
        entry_id="1",
        unique_id="airos_device",
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    mock_airos_class.assert_called_once_with(
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=ANY,
        use_ssl=False,
    )

    expect(entry.data[SECTION_ADVANCED_SETTINGS][CONF_SSL]).to_be(False)
    expect(entry.data[SECTION_ADVANCED_SETTINGS][CONF_VERIFY_SSL]).to_be(False)


@test
async def ssl_migrate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airos_client: MagicMock = Depends(mock_airos_client),
    mock_async_get_firmware_data: AsyncMock = Depends(mock_async_get_firmware_data),
) -> None:
    """Test migrate entry SSL options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=MOCK_CONFIG_V1,
        entry_id="1",
        unique_id="airos_device",
        version=1,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry.version).to_equal(2)
    expect(entry.minor_version).to_equal(1)
    expect(entry.data).to_equal(MOCK_CONFIG_V1_2)


@test.skip("indirect parametrize via sensor_domain/sensor_name/mock_id — keep skipped")
async def uid_migrate_entry() -> None:
    """Stub for test_uid_migrate_entry."""


@test
async def migrate_future_return(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airos_client: MagicMock = Depends(mock_airos_client),
    mock_async_get_firmware_data: AsyncMock = Depends(mock_async_get_firmware_data),
) -> None:
    """Test migrate entry unique id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=MOCK_CONFIG_V1_2,
        entry_id="1",
        unique_id="airos_device",
        version=3,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)


@test
async def load_unload_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_airos_client: MagicMock = Depends(mock_airos_client),
    mock_async_get_firmware_data: AsyncMock = Depends(mock_async_get_firmware_data),
) -> None:
    """Test setup and unload config entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "auth_error",
        exception=AirOSConnectionAuthenticationError,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "setup_error",
        exception=AirOSConnectionSetupError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "device_connection_error",
        exception=AirOSDeviceConnectionError,
        state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "key_data_missing",
        exception=AirOSKeyDataMissingError,
        state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "generic_exception",
        exception=Exception,
        state=ConfigEntryState.SETUP_ERROR,
    ),
)
async def setup_entry_failure(
    exception: type[Exception],
    state: ConfigEntryState,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_airos_class: MagicMock = Depends(mock_airos_class),
    mock_airos_client: MagicMock = Depends(mock_airos_client),
    mock_async_get_firmware_data: AsyncMock = Depends(mock_async_get_firmware_data),
) -> None:
    """Test config entry setup failure."""
    mock_async_get_firmware_data.side_effect = exception

    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
    expect(result).to_be(False)
    expect(mock_config_entry.state).to_equal(state)


@test
async def fetch_airos_data_auth_error(
    mock_airos_client: MagicMock = Depends(mock_airos_client),
) -> None:
    """Test login auth error triggers ConfigEntryAuthFailed."""
    mock_airos_client.login.side_effect = AirOSConnectionAuthenticationError

    async with expect_raises_async(ConfigEntryAuthFailed):
        await async_fetch_airos_data(mock_airos_client, mock_airos_client.status)
