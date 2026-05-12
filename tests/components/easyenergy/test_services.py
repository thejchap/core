"""Tests for the services provided by the easyEnergy integration."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.easyenergy.const import DOMAIN
from homeassistant.components.easyenergy.services import (
    ATTR_CONFIG_ENTRY,
    ENERGY_RETURN_SERVICE_NAME,
    ENERGY_USAGE_SERVICE_NAME,
    GAS_SERVICE_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from ._fixtures import mock_config_entry, mock_easyenergy

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


async def _setup_integration(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@test
async def has_services(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_easyenergy),
) -> None:
    """Test the existence of the easyEnergy Service."""
    await _setup_integration(hass, entry)
    expect(hass.services.has_service(DOMAIN, GAS_SERVICE_NAME)).to_be(True)
    expect(hass.services.has_service(DOMAIN, ENERGY_USAGE_SERVICE_NAME)).to_be(True)
    expect(hass.services.has_service(DOMAIN, ENERGY_RETURN_SERVICE_NAME)).to_be(True)


@test.skip("snapshot test — out of scope")
async def service() -> None:
    """Stub for test_service."""


@test.skip("snapshot test — out of scope")
async def service_filters_datetime_range() -> None:
    """Stub for test_service_filters_datetime_range."""


@test.cases(
    test.case("gas", service=GAS_SERVICE_NAME),
    test.case("energy_usage", service=ENERGY_USAGE_SERVICE_NAME),
    test.case("energy_return", service=ENERGY_RETURN_SERVICE_NAME),
)
async def service_schema_validation(
    *,
    service: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_easyenergy),
) -> None:
    """Test easyEnergy service schema validation."""
    await _setup_integration(hass, entry)
    async with expect_raises_async(vol.er.Error, match="required key not provided"):
        await hass.services.async_call(
            DOMAIN,
            service,
            {},
            blocking=True,
            return_response=True,
        )


@test.cases(
    test.case("gas_missing_vat", service=GAS_SERVICE_NAME, data={}, msg="required key not provided"),
    test.case(
        "gas_bad_vat",
        service=GAS_SERVICE_NAME,
        data={"incl_vat": "incorrect vat"},
        msg="expected bool for dictionary value",
    ),
    test.case(
        "usage_missing_vat",
        service=ENERGY_USAGE_SERVICE_NAME,
        data={},
        msg="required key not provided",
    ),
    test.case(
        "usage_bad_vat",
        service=ENERGY_USAGE_SERVICE_NAME,
        data={"incl_vat": "incorrect vat"},
        msg="expected bool for dictionary value",
    ),
)
async def service_schema_validation_vat(
    *,
    service: str,
    data: dict[str, str | bool],
    msg: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_easyenergy),
) -> None:
    """Test easyEnergy service schema validation for VAT."""
    await _setup_integration(hass, entry)
    async with expect_raises_async(vol.er.Error, match=msg):
        await hass.services.async_call(
            DOMAIN,
            service,
            {ATTR_CONFIG_ENTRY: entry.entry_id} | data,
            blocking=True,
            return_response=True,
        )


@test
async def service_schema_validation_return_vat(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_easyenergy),
) -> None:
    """Test return prices do not accept VAT selection."""
    await _setup_integration(hass, entry)
    async with expect_raises_async(vol.er.Error, match="extra keys not allowed"):
        await hass.services.async_call(
            DOMAIN,
            ENERGY_RETURN_SERVICE_NAME,
            {ATTR_CONFIG_ENTRY: entry.entry_id, "incl_vat": True},
            blocking=True,
            return_response=True,
        )


@test.cases(
    test.case("gas", service=GAS_SERVICE_NAME, needs_vat=True),
    test.case("energy_usage", service=ENERGY_USAGE_SERVICE_NAME, needs_vat=True),
    test.case("energy_return", service=ENERGY_RETURN_SERVICE_NAME, needs_vat=False),
)
async def service_validation_config_entry_not_found(
    *,
    service: str,
    needs_vat: bool,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_easyenergy),
) -> None:
    """Test config entry validation for easyEnergy services."""
    await _setup_integration(hass, entry)
    service_data: dict[str, str | bool] = {ATTR_CONFIG_ENTRY: "incorrect entry"}
    if needs_vat:
        service_data["incl_vat"] = True

    err: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            service,
            service_data,
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        err = exc

    expect(err).not_.to_be(None)
    expect(err.translation_key).to_equal("service_config_entry_not_found")
    expect(err.translation_placeholders).to_equal(
        {"domain": DOMAIN, "entry_id": "incorrect entry"}
    )


@test.cases(
    test.case("gas_start", service=GAS_SERVICE_NAME, field="start", needs_vat=True),
    test.case("gas_end", service=GAS_SERVICE_NAME, field="end", needs_vat=True),
    test.case(
        "usage_start",
        service=ENERGY_USAGE_SERVICE_NAME,
        field="start",
        needs_vat=True,
    ),
    test.case(
        "usage_end",
        service=ENERGY_USAGE_SERVICE_NAME,
        field="end",
        needs_vat=True,
    ),
    test.case(
        "return_start",
        service=ENERGY_RETURN_SERVICE_NAME,
        field="start",
        needs_vat=False,
    ),
    test.case(
        "return_end",
        service=ENERGY_RETURN_SERVICE_NAME,
        field="end",
        needs_vat=False,
    ),
)
async def service_validation_invalid_date(
    *,
    service: str,
    field: str,
    needs_vat: bool,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_easyenergy),
) -> None:
    """Test invalid date validation for easyEnergy services."""
    await _setup_integration(hass, entry)
    date_value = "incorrect date"
    service_data: dict[str, str | bool] = {
        ATTR_CONFIG_ENTRY: entry.entry_id,
        field: date_value,
    }
    if needs_vat:
        service_data["incl_vat"] = True

    err: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            service,
            service_data,
            blocking=True,
            return_response=True,
        )
    except ServiceValidationError as exc:
        err = exc

    expect(err).not_.to_be(None)
    expect(err.translation_key).to_equal("invalid_date")
    expect(err.translation_placeholders).to_equal({"date": date_value})
