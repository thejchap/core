"""Test the Coinbase config flow."""

from unittest.mock import patch

from coinbase.rest.rest_base import HTTPError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.coinbase.const import (
    CONF_CURRENCIES,
    CONF_EXCHANGE_PRECISION,
    CONF_EXCHANGE_RATES,
    DOMAIN,
)
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .common import (
    init_mock_coinbase,
    mock_get_exchange_rates,
    mock_get_portfolios,
    mocked_get_accounts_v3,
)
from .const import BAD_CURRENCY, BAD_EXCHANGE_RATE, GOOD_CURRENCY, GOOD_EXCHANGE_RATE

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch("coinbase.rest.RESTClient.get_accounts", new=mocked_get_accounts_v3),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": mock_get_exchange_rates()},
        ),
        patch(
            "homeassistant.components.coinbase.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "123456", CONF_API_TOKEN: "AbCDeF"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Default")
    expect(result2["data"]).to_equal(
        {CONF_API_KEY: "123456", CONF_API_TOKEN: "AbCDeF"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.skip("uses caplog text inspection")
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "coinbase.rest.RESTClient.get_portfolios",
        side_effect=ConnectionError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "123456", CONF_API_TOKEN: "AbCDeF"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_catch_all_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unknown exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "coinbase.rest.RESTClient.get_portfolios",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "123456", CONF_API_TOKEN: "AbCDeF"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def option_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a good wallet currency option."""
    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch("coinbase.rest.RESTClient.get_accounts", new=mocked_get_accounts_v3),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": mock_get_exchange_rates()},
        ),
    ):
        config_entry = await init_mock_coinbase(hass)
        await hass.async_block_till_done()
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_CURRENCIES: [GOOD_CURRENCY],
                CONF_EXCHANGE_RATES: [GOOD_EXCHANGE_RATE],
                CONF_EXCHANGE_PRECISION: 5,
            },
        )
        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        await hass.async_block_till_done()


@test
async def form_bad_account_currency(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a bad currency option."""
    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch("coinbase.rest.RESTClient.get_accounts", new=mocked_get_accounts_v3),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": mock_get_exchange_rates()},
        ),
    ):
        config_entry = await init_mock_coinbase(hass)
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_CURRENCIES: [BAD_CURRENCY],
                CONF_EXCHANGE_RATES: [],
                CONF_EXCHANGE_PRECISION: 5,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "currency_unavailable"})


@test
async def form_bad_exchange_rate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a bad exchange rate."""
    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch("coinbase.rest.RESTClient.get_accounts", new=mocked_get_accounts_v3),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": mock_get_exchange_rates()},
        ),
    ):
        config_entry = await init_mock_coinbase(hass)
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_CURRENCIES: [],
                CONF_EXCHANGE_RATES: [BAD_EXCHANGE_RATE],
                CONF_EXCHANGE_PRECISION: 5,
            },
        )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "exchange_rate_unavailable"})


@test
async def option_catch_all_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle an unknown exception in the option flow."""
    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch("coinbase.rest.RESTClient.get_accounts", new=mocked_get_accounts_v3),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": mock_get_exchange_rates()},
        ),
    ):
        config_entry = await init_mock_coinbase(hass)
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()

    with patch(
        "coinbase.rest.RESTClient.get_accounts",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_CURRENCIES: [],
                CONF_EXCHANGE_RATES: ["ETH"],
                CONF_EXCHANGE_PRECISION: 5,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch("coinbase.rest.RESTClient.get_accounts", new=mocked_get_accounts_v3),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": mock_get_exchange_rates()},
        ),
    ):
        config_entry = await init_mock_coinbase(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": config_entry.entry_id,
        },
        data=config_entry.data,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch("coinbase.rest.RESTClient.get_accounts", new=mocked_get_accounts_v3),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": mock_get_exchange_rates()},
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "new_key", CONF_API_TOKEN: "new_secret"},
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("new_key")
    expect(config_entry.data[CONF_API_TOKEN]).to_equal("new_secret")


@test
async def reauth_flow_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow with invalid credentials."""
    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch("coinbase.rest.RESTClient.get_accounts", new=mocked_get_accounts_v3),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": mock_get_exchange_rates()},
        ),
    ):
        config_entry = await init_mock_coinbase(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": config_entry.entry_id,
        },
        data=config_entry.data,
    )

    api_auth_error_key = HTTPError("invalid api key")
    with patch(
        "coinbase.rest.RESTClient.get_portfolios",
        side_effect=api_auth_error_key,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "bad_key", CONF_API_TOKEN: "bad_secret"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["errors"]).to_equal({"base": "invalid_auth_key"})
