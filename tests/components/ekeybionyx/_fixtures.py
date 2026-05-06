"""Tryke fixtures for ekey bionyx tests."""

from collections.abc import Generator
from http import HTTPStatus
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.ekeybionyx.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import aioclient_mock, hass as hass_fixture
from tests.test_util.aiohttp import AiohttpClientMocker

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"


def dummy_systems(
    num_systems: int, free_wh: int, used_wh: int, own_system: bool = True
) -> list[dict]:
    """Create dummy systems."""
    return [
        {
            "systemName": f"System {i + 1}",
            "systemId": f"946DA01F-9ABD-4D9D-80C7-02AF85C822A{i + 8}",
            "ownSystem": own_system,
            "functionWebhookQuotas": {"free": free_wh, "used": used_wh},
        }
        for i in range(num_systems)
    ]


@fixture
def system(client_mock: AiohttpClientMocker = Depends(aioclient_mock)) -> None:
    """Fixture to setup fake requests made to Ekey Bionyx API during config flow."""
    client_mock.get(
        "https://api.bionyx.io/3rd-party/api/systems",
        json=dummy_systems(2, 5, 0),
    )


@fixture
def no_own_system(
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Fixture to setup fake requests made to Ekey Bionyx API during config flow."""
    client_mock.get(
        "https://api.bionyx.io/3rd-party/api/systems",
        json=dummy_systems(1, 1, 0, False),
    )


@fixture
def no_response(client_mock: AiohttpClientMocker = Depends(aioclient_mock)) -> None:
    """Fixture to setup fake requests made to Ekey Bionyx API during config flow."""
    client_mock.get(
        "https://api.bionyx.io/3rd-party/api/systems",
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@fixture
def no_available_webhooks(
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Fixture to setup fake requests made to Ekey Bionyx API during config flow."""
    client_mock.get(
        "https://api.bionyx.io/3rd-party/api/systems",
        json=dummy_systems(1, 0, 0),
    )


@fixture
def already_set_up(
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Fixture to setup fake requests made to Ekey Bionyx API during config flow."""
    client_mock.get(
        "https://api.bionyx.io/3rd-party/api/systems",
        json=dummy_systems(1, 0, 1),
    )


@fixture
def webhooks(client_mock: AiohttpClientMocker = Depends(aioclient_mock)) -> None:
    """Fixture to setup fake requests made to Ekey Bionyx API during config flow."""
    client_mock.get(
        "https://api.bionyx.io/3rd-party/api/systems/946DA01F-9ABD-4D9D-80C7-02AF85C822A8/function-webhooks",
        json=[
            {
                "functionWebhookId": "946DA01F-9ABD-4D9D-80C7-02AF85C822B9",
                "integrationName": "Home Assistant",
                "locationName": "A simple string containing 0 to 128 word, space and punctuation characters.",
                "functionName": "A simple string containing 0 to 50 word, space and punctuation characters.",
                "expiresAt": "2022-05-16T04:11:28.0000000+00:00",
                "modificationState": None,
            }
        ],
    )


@fixture
def webhook_deletion(
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Fixture to setup fake requests made to Ekey Bionyx API during config flow."""
    client_mock.delete(
        "https://api.bionyx.io/3rd-party/api/systems/946DA01F-9ABD-4D9D-80C7-02AF85C822A8/function-webhooks/946DA01F-9ABD-4D9D-80C7-02AF85C822B9",
        status=HTTPStatus.ACCEPTED,
    )


@fixture
def add_webhook(
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Fixture to setup fake requests made to Ekey Bionyx API during config flow."""
    client_mock.post(
        "https://api.bionyx.io/3rd-party/api/systems/946DA01F-9ABD-4D9D-80C7-02AF85C822A8/function-webhooks",
        status=HTTPStatus.CREATED,
        json={
            "functionWebhookId": "946DA01F-9ABD-4D9D-80C7-02AF85C822A8",
            "integrationName": "Home Assistant",
            "locationName": "Home Assistant",
            "functionName": "Test",
            "expiresAt": "2022-05-16T04:11:28.0000000+00:00",
            "modificationState": None,
        },
    )


@fixture
def webhook_id() -> Generator[None]:
    """Mock webhook_id."""
    with patch(
        "homeassistant.components.ekeybionyx.config_flow.webhook_generate_id",
        return_value="1234567890",
    ):
        yield


@fixture
def token_hex() -> Generator[None]:
    """Mock auth property."""
    with patch(
        "secrets.token_hex",
        return_value="f2156edca7fc6871e13845314a6fc68622e5ad7c58f17663a487ed28cac247f7",
    ):
        yield


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Fixture to setup credentials."""
    assert await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )
