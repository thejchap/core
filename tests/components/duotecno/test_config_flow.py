"""Test the duotecno config flow."""

from unittest.mock import AsyncMock, patch

from duotecno.exceptions import InvalidPassword
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.duotecno.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.duotecno._fixtures import mock_setup_entry
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
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

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("1.1.1.1")
    expect(result2["data"]).to_equal(
        {
            "host": "1.1.1.1",
            "port": 1234,
            "password": "test-password",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_password", InvalidPassword, "invalid_auth"),
    test.case("connection_error", ConnectionError, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def invalid(
    test_side_effect: type[Exception],
    test_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
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
    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
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
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
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

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")
