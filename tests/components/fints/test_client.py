"""Tests for the FinTS client."""

from fints.client import BankIdentifier, FinTSOperations
from tryke import expect, test

from homeassistant.components.fints.sensor import (
    BankCredentials,
    FinTsClient,
    SEPAAccount,
)

BANK_INFORMATION = {
    "bank_identifier": BankIdentifier(country_identifier="280", bank_code="50010517"),
    "currency": "EUR",
    "customer_id": "0815",
    "owner_name": ["SURNAME, FIRSTNAME"],
    "subaccount_number": None,
    "supported_operations": {
        FinTSOperations.GET_BALANCE: True,
        FinTSOperations.GET_CREDIT_CARD_TRANSACTIONS: False,
        FinTSOperations.GET_HOLDINGS: False,
        FinTSOperations.GET_SCHEDULED_DEBITS_MULTIPLE: False,
        FinTSOperations.GET_SCHEDULED_DEBITS_SINGLE: False,
        FinTSOperations.GET_SEPA_ACCOUNTS: True,
        FinTSOperations.GET_STATEMENT: False,
        FinTSOperations.GET_STATEMENT_PDF: False,
        FinTSOperations.GET_TRANSACTIONS: True,
        FinTSOperations.GET_TRANSACTIONS_XML: False,
    },
}


@test.cases(
    test.case(
        "valid_balance_account",
        account_number="GIRO1",
        iban="GIRO1",
        product_name="Valid balance account",
        account_type=5,
        expected_balance_result=True,
        expected_holdings_result=False,
    ),
    test.case(
        "invalid_account",
        account_number=None,
        iban=None,
        product_name="Invalid account",
        account_type=None,
        expected_balance_result=False,
        expected_holdings_result=False,
    ),
    test.case(
        "account_without_type",
        account_number="GIRO2",
        iban="GIRO2",
        product_name="Account without type",
        account_type=None,
        expected_balance_result=False,
        expected_holdings_result=False,
    ),
    test.case(
        "balance_account_from_fallback",
        account_number="GIRO3",
        iban="GIRO3",
        product_name="Balance account from fallback",
        account_type=None,
        expected_balance_result=True,
        expected_holdings_result=False,
    ),
    test.case(
        "valid_holdings_account",
        account_number="DEPOT1",
        iban="DEPOT1",
        product_name="Valid holdings account",
        account_type=33,
        expected_balance_result=False,
        expected_holdings_result=True,
    ),
    test.case(
        "holdings_account_from_fallback",
        account_number="DEPOT2",
        iban="DEPOT2",
        product_name="Holdings account from fallback",
        account_type=None,
        expected_balance_result=False,
        expected_holdings_result=True,
    ),
)
async def account_type(
    *,
    account_number: str | None,
    iban: str | None,
    product_name: str,
    account_type: int | None,
    expected_balance_result: bool,
    expected_holdings_result: bool,
) -> None:
    """Check client methods is_balance_account and is_holdings_account."""
    credentials = BankCredentials(
        blz=1234, login="test", pin="0000", url="https://example.com"
    )
    account_config = {"GIRO3": True}
    holdings_config = {"DEPOT2": True}

    client = FinTsClient(
        credentials=credentials,
        name="test",
        account_config=account_config,
        holdings_config=holdings_config,
    )

    client._account_information_fetched = True
    client._account_information = {
        iban: BANK_INFORMATION
        | {
            "account_number": account_number,
            "iban": iban,
            "product_name": product_name,
            "type": account_type,
        }
    }

    sepa_account = SEPAAccount(
        iban=iban,
        bic="BANCODELTEST",
        accountnumber=account_number,
        subaccount=None,
        blz="12345",
    )

    expect(client.is_balance_account(sepa_account)).to_equal(expected_balance_result)
    expect(client.is_holdings_account(sepa_account)).to_equal(expected_holdings_result)
