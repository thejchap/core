"""Test account link services."""

import asyncio
from collections.abc import Generator
import logging
from time import time
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.cloud import account_link
from homeassistant.components.cloud.const import DATA_CLOUD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.util.dt import utcnow

from ._fixtures import load_homeassistant

from tests.common import MockConfigEntry, async_fire_time_changed, mock_platform
from tests.hass_fixtures import (
    current_request_with_host,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async

TEST_DOMAIN = "oauth2_test"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@fixture
def flow_handler(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[type[config_entry_oauth2_flow.AbstractOAuth2FlowHandler]]:
    """Return a registered config flow."""

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")

    class TestFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler):
        """Test flow handler."""

        DOMAIN = TEST_DOMAIN

        @property
        def logger(self) -> logging.Logger:
            """Return logger."""
            return logging.getLogger(__name__)

    with patch.dict(config_entries.HANDLERS, {TEST_DOMAIN: TestFlowHandler}):
        yield TestFlowHandler


@test
async def setup_provide_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we provide implementations."""
    legacy_entry = MockConfigEntry(
        domain="legacy",
        version=1,
        data={"auth_implementation": "cloud"},
    )
    none_cloud_entry = MockConfigEntry(
        domain="no_cloud",
        version=1,
        data={"auth_implementation": "somethingelse"},
    )
    none_cloud_entry.add_to_hass(hass)
    legacy_entry.add_to_hass(hass)
    account_link.async_setup(hass)

    with (
        patch(
            "homeassistant.components.cloud.account_link._get_services",
            return_value=[
                {"service": "test", "min_version": "0.1.0"},
                {"service": "too_new", "min_version": "1000000.0.0"},
                {"service": "dev", "min_version": "2022.9.0"},
                {
                    "service": "deprecated",
                    "min_version": "0.1.0",
                    "accepts_new_authorizations": False,
                },
                {
                    "service": "legacy",
                    "min_version": "0.1.0",
                    "accepts_new_authorizations": False,
                },
                {
                    "service": "no_cloud",
                    "min_version": "0.1.0",
                    "accepts_new_authorizations": False,
                },
            ],
        ),
        patch(
            "homeassistant.components.cloud.account_link.HA_VERSION",
            "2022.9.0.dev20220817",
        ),
    ):
        expect(
            await config_entry_oauth2_flow.async_get_implementations(
                hass, "non_existing"
            )
        ).to_equal({})
        expect(
            await config_entry_oauth2_flow.async_get_implementations(hass, "too_new")
        ).to_equal({})
        expect(
            await config_entry_oauth2_flow.async_get_implementations(hass, "deprecated")
        ).to_equal({})
        expect(
            await config_entry_oauth2_flow.async_get_implementations(hass, "no_cloud")
        ).to_equal({})

        implementations = await config_entry_oauth2_flow.async_get_implementations(
            hass, "test"
        )

        legacy_implementations = (
            await config_entry_oauth2_flow.async_get_implementations(hass, "legacy")
        )

        dev_implementations = await config_entry_oauth2_flow.async_get_implementations(
            hass, "dev"
        )

    expect("cloud" in implementations).to_be(True)
    expect(implementations["cloud"].domain).to_equal("cloud")
    expect(implementations["cloud"].service).to_equal("test")
    expect(implementations["cloud"].hass is hass).to_be(True)

    expect("cloud" in legacy_implementations).to_be(True)
    expect(legacy_implementations["cloud"].domain).to_equal("cloud")
    expect(legacy_implementations["cloud"].service).to_equal("legacy")
    expect(legacy_implementations["cloud"].hass is hass).to_be(True)

    expect("cloud" in dev_implementations).to_be(True)
    expect(dev_implementations["cloud"].domain).to_equal("cloud")
    expect(dev_implementations["cloud"].service).to_equal("dev")
    expect(dev_implementations["cloud"].hass is hass).to_be(True)


@test
async def get_services_cached(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we cache services."""
    hass.data[DATA_CLOUD] = None

    services = 1

    with (
        patch.object(account_link, "CACHE_TIMEOUT", 0),
        patch(
            "hass_nabucasa.account_link.async_fetch_available_services",
            side_effect=lambda _: services,
        ) as mock_fetch,
    ):
        expect(await account_link._get_services(hass)).to_equal(1)

        services = 2

        expect(len(mock_fetch.mock_calls)).to_equal(1)
        expect(await account_link._get_services(hass)).to_equal(1)

        services = 3
        hass.data.pop(account_link.DATA_SERVICES)
        expect(await account_link._get_services(hass)).to_equal(3)

        services = 4
        async_fire_time_changed(hass, utcnow())
        await hass.async_block_till_done()

        # Check cache purged
        expect(await account_link._get_services(hass)).to_equal(4)


@test
async def get_services_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we cache services."""
    hass.data[DATA_CLOUD] = None

    with (
        patch.object(account_link, "CACHE_TIMEOUT", 0),
        patch(
            "hass_nabucasa.account_link.async_fetch_available_services",
            side_effect=TimeoutError,
        ),
    ):
        async with expect_raises_async(
            config_entry_oauth2_flow.ImplementationUnavailableError
        ):
            await account_link._get_services(hass)


@test
async def implementation(
    _request: None = Depends(current_request_with_host),
    handler: type[config_entry_oauth2_flow.AbstractOAuth2FlowHandler] = Depends(
        flow_handler
    ),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Cloud OAuth2 implementation."""
    hass.data[DATA_CLOUD] = None

    impl = account_link.CloudOAuth2Implementation(hass, "test")
    expect(impl.name).to_equal("Home Assistant Cloud")
    expect(impl.domain).to_equal("cloud")

    handler.async_register_implementation(hass, impl)

    flow_finished = asyncio.Future()

    helper = Mock(
        async_get_authorize_url=AsyncMock(return_value="http://example.com/auth"),
        async_get_tokens=Mock(return_value=flow_finished),
    )

    with patch(
        "hass_nabucasa.account_link.AuthorizeAccountHelper", return_value=helper
    ):
        result = await hass.config_entries.flow.async_init(
            TEST_DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal("http://example.com/auth")

    flow_finished.set_result(
        {
            "refresh_token": "mock-refresh",
            "access_token": "mock-access",
            "expires_in": 10,
            "token_type": "bearer",
        }
    )
    await hass.async_block_till_done()

    # Flow finished!
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["data"]["auth_implementation"]).to_equal("cloud")

    expires_at = result["data"]["token"].pop("expires_at")
    expect(round(expires_at - time())).to_equal(10)

    expect(result["data"]["token"]).to_equal(
        {
            "refresh_token": "mock-refresh",
            "access_token": "mock-access",
            "token_type": "bearer",
            "expires_in": 10,
        }
    )

    entry = hass.config_entries.async_entries(TEST_DOMAIN)[0]

    expect(
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
        is impl
    ).to_be(True)
