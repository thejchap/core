"""Tryke fixtures for the SwitchBot integration."""

from collections.abc import Callable

from tryke import fixture

from homeassistant.components.switchbot.const import (
    CONF_CURTAIN_SPEED,
    CONF_ENCRYPTION_KEY,
    CONF_KEY_ID,
    CONF_RETRY_COUNT,
    DEFAULT_CURTAIN_SPEED,
    DEFAULT_RETRY_COUNT,
    DOMAIN,
    SupportedModels,
)
from homeassistant.const import CONF_ADDRESS, CONF_NAME, CONF_SENSOR_TYPE

from tests.common import MockConfigEntry


@fixture
def mock_entry_factory() -> Callable[[str], MockConfigEntry]:
    """Build a MockConfigEntry with a customizable sensor type."""

    def _create_entry(sensor_type: str = "curtain") -> MockConfigEntry:
        options: dict[str, int] = {CONF_RETRY_COUNT: DEFAULT_RETRY_COUNT}
        if sensor_type == SupportedModels.CURTAIN:
            options[CONF_CURTAIN_SPEED] = DEFAULT_CURTAIN_SPEED
        return MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
                CONF_NAME: "test-name",
                CONF_SENSOR_TYPE: sensor_type,
            },
            unique_id="aabbccddeeff",
            version=1,
            minor_version=2,
            options=options,
        )

    return _create_entry


@fixture
def mock_entry_encrypted_factory() -> Callable[[str], MockConfigEntry]:
    """Build an encrypted MockConfigEntry with a customizable sensor type."""

    def _create_entry(sensor_type: str = "lock") -> MockConfigEntry:
        options: dict[str, int] = {CONF_RETRY_COUNT: DEFAULT_RETRY_COUNT}
        if sensor_type == SupportedModels.CURTAIN:
            options[CONF_CURTAIN_SPEED] = DEFAULT_CURTAIN_SPEED
        return MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
                CONF_NAME: "test-name",
                CONF_SENSOR_TYPE: sensor_type,
                CONF_KEY_ID: "ff",
                CONF_ENCRYPTION_KEY: "ffffffffffffffffffffffffffffffff",
            },
            unique_id="aabbccddeeff",
            version=1,
            minor_version=2,
            options=options,
        )

    return _create_entry
