"""Test the duotecno config flow."""

from unittest.mock import AsyncMock, patch

from duotecno.exceptions import InvalidPassword
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.duotecno.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "duotecno.controller.PyDuotecno.connect",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 1234,
                "password": "test-password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.1.1.1")
    expect(result2["data"]).to_equal(
        {
            "host": "1.1.1.1",
            "port": 1234,
            "password": "test-password",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth", test_side_effect=InvalidPassword, test_error="invalid_auth"
    ),
    test.case(
        "cannot_connect", test_side_effect=ConnectionError, test_error="cannot_connect"
    ),
    test.case("unknown", test_side_effect=Exception, test_error="unknown"),
)
async def invalid(
    test_side_effect: type[Exception],
    test_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test all side_effects on the controller.connect via parameters."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("duotecno.controller.PyDuotecno.connect", side_effect=test_side_effect):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 1234,
                "password": "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": test_error})

    with patch("duotecno.controller.PyDuotecno.connect"):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "port": 1234,
                "password": "test-password2",
            },
        )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.1.1.1")
    expect(result2["data"]).to_equal(
        {
            "host": "1.1.1.1",
            "port": 1234,
            "password": "test-password2",
        }
    )


@test
async def already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test duoteco flow - already setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="duotecno_1234",
        data={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
