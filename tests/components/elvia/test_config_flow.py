"""Test the Elvia config flow."""

from unittest.mock import AsyncMock, patch

from elvia import error as ElviaError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.elvia.const import CONF_METERING_POINT_ID, DOMAIN
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, UnknownFlow

from ._fixtures import mock_setup_entry, recorder_mock

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async

TEST_API_TOKEN = "xxx-xxx-xxx-xxx"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def single_metering_point(
    _trigger: None = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test using the config flow with a single metering point."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "elvia.meter_value.MeterValue.get_meter_values",
        return_value={"meteringpoints": [{"meteringPointId": "1234"}]},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_TOKEN: TEST_API_TOKEN,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1234")
    expect(result["data"]).to_equal(
        {
            CONF_API_TOKEN: TEST_API_TOKEN,
            CONF_METERING_POINT_ID: "1234",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def multiple_metering_points(
    _trigger: None = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test using the config flow with multiple metering points."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "elvia.meter_value.MeterValue.get_meter_values",
        return_value={
            "meteringpoints": [
                {"meteringPointId": "1234"},
                {"meteringPointId": "5678"},
            ]
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_TOKEN: TEST_API_TOKEN,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("select_meter")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_METERING_POINT_ID: "5678",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("5678")
    expect(result["data"]).to_equal(
        {
            CONF_API_TOKEN: TEST_API_TOKEN,
            CONF_METERING_POINT_ID: "5678",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def no_metering_points(
    _trigger: None = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test using the config flow with no metering points."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "elvia.meter_value.MeterValue.get_meter_values",
        return_value={"meteringpoints": []},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_TOKEN: TEST_API_TOKEN,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_metering_points")
    expect(len(mock_setup.mock_calls)).to_equal(0)


@test
async def bad_data(
    _trigger: None = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test using the config flow with bad data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "elvia.meter_value.MeterValue.get_meter_values",
        return_value={},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_TOKEN: TEST_API_TOKEN,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_metering_points")
    expect(len(mock_setup.mock_calls)).to_equal(0)


@test
async def abort_when_metering_point_id_exist(
    _trigger: None = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that we abort when the metering point ID exists."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1234",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "elvia.meter_value.MeterValue.get_meter_values",
        return_value={"meteringpoints": [{"meteringPointId": "1234"}]},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_TOKEN: TEST_API_TOKEN,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("metering_point_id_already_configured")
    expect(len(mock_setup.mock_calls)).to_equal(0)


@test.cases(
    test.case(
        "elvia_exception",
        side_effect=ElviaError.ElviaException("Boom"),
        base_error="unknown",
    ),
    test.case(
        "auth_error",
        side_effect=ElviaError.AuthError("Boom", 403, {}, ""),
        base_error="invalid_auth",
    ),
    test.case(
        "server_exception",
        side_effect=ElviaError.ElviaServerException("Boom", 500, {}, ""),
        base_error="unknown",
    ),
    test.case(
        "client_exception",
        side_effect=ElviaError.ElviaClientException("Boom"),
        base_error="unknown",
    ),
)
async def form_exceptions(
    *,
    side_effect: Exception,
    base_error: str,
    _trigger: None = Depends(_trigger_executor),
    _recorder=Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle errors during config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "elvia.meter_value.MeterValue.get_meter_values",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_TOKEN: TEST_API_TOKEN,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": base_error})

    # Simulate that the user gives up and closes the window...
    hass.config_entries.flow._async_remove_flow_progress(result["flow_id"])
    await hass.async_block_till_done()

    async with expect_raises_async(UnknownFlow):
        hass.config_entries.flow.async_get(result["flow_id"])
