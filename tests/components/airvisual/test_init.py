"""Define tests for AirVisual init."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.airvisual import (
    CONF_CITY,
    CONF_GEOGRAPHIES,
    CONF_INTEGRATION_TYPE,
    DOMAIN,
    INTEGRATION_TYPE_GEOGRAPHY_COORDS,
    INTEGRATION_TYPE_GEOGRAPHY_NAME,
    INTEGRATION_TYPE_NODE_PRO,
)

# pylint: disable-next=hass-component-root-import
from homeassistant.components.airvisual_pro.const import DOMAIN as AIRVISUAL_PRO_DOMAIN
from homeassistant.const import (
    CONF_API_KEY,
    CONF_COUNTRY,
    CONF_IP_ADDRESS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_STATE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, issue_registry as ir

from ._fixtures import (
    COORDS_CONFIG,
    COORDS_CONFIG2,
    NAME_CONFIG,
    TEST_API_KEY,
    TEST_CITY,
    TEST_COUNTRY,
    TEST_LATITUDE,
    TEST_LATITUDE2,
    TEST_LONGITUDE,
    TEST_LONGITUDE2,
    TEST_STATE,
    mock_pyairvisual,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def migration_1_2(
    _network: None = Depends(mock_network),
    _mock: None = Depends(mock_pyairvisual),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migrating from version 1 to 2."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_API_KEY,
        data={
            CONF_API_KEY: TEST_API_KEY,
            CONF_GEOGRAPHIES: [
                {
                    CONF_LATITUDE: TEST_LATITUDE,
                    CONF_LONGITUDE: TEST_LONGITUDE,
                },
                {
                    CONF_CITY: TEST_CITY,
                    CONF_STATE: TEST_STATE,
                    CONF_COUNTRY: TEST_COUNTRY,
                },
                {
                    CONF_LATITUDE: TEST_LATITUDE2,
                    CONF_LONGITUDE: TEST_LONGITUDE2,
                },
            ],
        },
        version=1,
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    config_entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(config_entries)).to_equal(3)

    identifier1 = f"{TEST_LATITUDE}, {TEST_LONGITUDE}"
    expect(config_entries[0].unique_id).to_equal(identifier1)
    expect(config_entries[0].title).to_equal(f"Cloud API ({identifier1})")
    expect(config_entries[0].data).to_equal(
        {**COORDS_CONFIG, CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_COORDS}
    )

    identifier2 = f"{TEST_CITY}, {TEST_STATE}, {TEST_COUNTRY}"
    expect(config_entries[1].unique_id).to_equal(identifier2)
    expect(config_entries[1].title).to_equal(f"Cloud API ({identifier2})")
    expect(config_entries[1].data).to_equal(
        {**NAME_CONFIG, CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_NAME}
    )

    identifier3 = f"{TEST_LATITUDE2}, {TEST_LONGITUDE2}"
    expect(config_entries[2].unique_id).to_equal(identifier3)
    expect(config_entries[2].title).to_equal(f"Cloud API ({identifier3})")
    expect(config_entries[2].data).to_equal(
        {**COORDS_CONFIG2, CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_GEOGRAPHY_COORDS}
    )


@test
async def migration_2_3(
    _network: None = Depends(mock_network),
    _mock: None = Depends(mock_pyairvisual),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test migrating from version 2 to 3."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="192.168.1.100",
        data={
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_PASSWORD: "abcde12345",
            CONF_INTEGRATION_TYPE: INTEGRATION_TYPE_NODE_PRO,
        },
        version=2,
    )
    entry.add_to_hass(hass)

    device_registry.async_get_or_create(
        name="192.168.1.100",
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "SERIAL_NUMBER")},
    )

    with patch(
        "homeassistant.components.airvisual.automation.automations_with_device",
        return_value=["automation.test_automation"],
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        for domain, entry_count in ((DOMAIN, 0), (AIRVISUAL_PRO_DOMAIN, 1)):
            expect(len(hass.config_entries.async_entries(domain))).to_equal(entry_count)

        expect(len(issue_registry.issues)).to_equal(1)
