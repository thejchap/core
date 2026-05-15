"""Test the Coinbase integration."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.coinbase import create_and_update_instance
from homeassistant.components.coinbase.const import (
    API_TYPE_VAULT,
    CONF_CURRENCIES,
    CONF_EXCHANGE_RATES,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import entity_registry as er

from .common import (
    init_mock_coinbase,
    mock_get_exchange_rates,
    mock_get_portfolios,
    mocked_get_accounts_v3,
)
from .const import (
    GOOD_CURRENCY,
    GOOD_CURRENCY_2,
    GOOD_EXCHANGE_RATE,
    GOOD_EXCHANGE_RATE_2,
)

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test successful unload of entry."""
    with (
        patch(
            "coinbase.rest.RESTClient.get_portfolios",
            return_value=mock_get_portfolios(),
        ),
        patch(
            "coinbase.rest.RESTClient.get_accounts",
            new=mocked_get_accounts_v3,
        ),
        patch(
            "coinbase.rest.RESTClient.get",
            return_value={"data": {"rates": {}}},
        ),
    ):
        entry = await init_mock_coinbase(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state is ConfigEntryState.LOADED).to_be(True)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(hass.data.get(DOMAIN)).to_be_falsy()


@test
async def option_updates(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test handling option updates."""

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
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_CURRENCIES: [GOOD_CURRENCY, GOOD_CURRENCY_2],
                CONF_EXCHANGE_RATES: [GOOD_EXCHANGE_RATE, GOOD_EXCHANGE_RATE_2],
            },
        )
        await hass.async_block_till_done()

        entities = er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        )
        expect(len(entities)).to_equal(4)
        currencies = [
            entity.unique_id.split("-")[-1]
            for entity in entities
            if "wallet" in entity.unique_id
        ]

        rates = [
            entity.unique_id.split("-")[-1]
            for entity in entities
            if "xe" in entity.unique_id
        ]

        expect(currencies).to_equal([GOOD_CURRENCY, GOOD_CURRENCY_2])
        expect(rates).to_equal([GOOD_EXCHANGE_RATE, GOOD_EXCHANGE_RATE_2])

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_CURRENCIES: [GOOD_CURRENCY],
                CONF_EXCHANGE_RATES: [GOOD_EXCHANGE_RATE],
            },
        )
        await hass.async_block_till_done()

        entities = er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        )
        expect(len(entities)).to_equal(2)
        currencies = [
            entity.unique_id.split("-")[-1]
            for entity in entities
            if "wallet" in entity.unique_id
        ]

        rates = [
            entity.unique_id.split("-")[-1]
            for entity in entities
            if "xe" in entity.unique_id
        ]

        expect(currencies).to_equal([GOOD_CURRENCY])
        expect(rates).to_equal([GOOD_EXCHANGE_RATE])


@test
async def ignore_vaults_wallets(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test vaults are ignored in wallet sensors."""

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
        config_entry = await init_mock_coinbase(hass, currencies=[GOOD_CURRENCY])
        await hass.async_block_till_done()

        entities = er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        )
        expect(len(entities)).to_equal(1)
        entity = entities[0]
        expect(API_TYPE_VAULT not in entity.original_name.lower()).to_be(True)


@test
async def v2_api_credentials_trigger_reauth(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that v2 API credentials trigger a reauth flow."""

    config_entry_data = {
        CONF_API_KEY: "v2_api_key_legacy_format",
        CONF_API_TOKEN: "v2_api_secret",
    }

    class MockEntry:
        def __init__(self, data: dict) -> None:
            self.data = data
            self.options: dict = {}

    entry = MockEntry(config_entry_data)

    raised: ConfigEntryAuthFailed | None = None
    try:
        create_and_update_instance(entry)
    except ConfigEntryAuthFailed as err:
        raised = err

    expect(raised is not None).to_be(True)
    expect("deprecated v2 API" in str(raised)).to_be(True)


@test
async def v3_api_credentials_work(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that v3 API credentials with 'organizations' don't trigger reauth."""

    config_entry_data = {
        CONF_API_KEY: "organizations_v3_api_key",
        CONF_API_TOKEN: "v3_api_secret",
    }

    class MockEntry:
        def __init__(self, data: dict) -> None:
            self.data = data
            self.options: dict = {}

    entry = MockEntry(config_entry_data)

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
        instance = create_and_update_instance(entry)
        expect(instance is not None).to_be(True)
