"""Test the Loqed config flow."""

from ipaddress import ip_address
import json
from unittest.mock import Mock, patch

import aiohttp
from loqedAPI import loqed
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.loqed.const import DOMAIN
from homeassistant.const import CONF_API_TOKEN, CONF_NAME, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import async_load_fixture
from tests.hass_fixtures import (
    aioclient_mock,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

zeroconf_data = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.12.34"),
    ip_addresses=[ip_address("192.168.12.34")],
    hostname="LOQED-ffeeddccbbaa.local",
    name="mock_name",
    port=9123,
    properties={},
    type="mock_type",
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def create_entry_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get can create a lock via zeroconf."""
    lock_result = json.loads(await async_load_fixture(hass, "status_ok.json", DOMAIN))

    with patch(
        "loqedAPI.loqed.LoqedAPI.async_get_lock_details",
        return_value=lock_result,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=zeroconf_data,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"] is None).to_be(True)

    mock_lock = Mock(spec=loqed.Lock, id="Foo")
    webhook_id = "Webhook_ID"
    all_locks_response = json.loads(
        await async_load_fixture(hass, "get_all_locks.json", DOMAIN)
    )

    with (
        patch(
            "loqedAPI.cloud_loqed.LoqedCloudAPI.async_get_locks",
            return_value=all_locks_response,
        ),
        patch(
            "loqedAPI.loqed.LoqedAPI.async_get_lock",
            return_value=mock_lock,
        ),
        patch(
            "homeassistant.components.loqed.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.webhook.async_generate_id",
            return_value=webhook_id,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_TOKEN: "eyadiuyfasiuasf",
            },
        )
        await hass.async_block_till_done()
    found_lock = all_locks_response["data"][0]

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("LOQED Touch Smart Lock")
    expect(result2["data"]).to_equal({
        "id": "Foo",
        "lock_key_key": found_lock["key_secret"],
        "bridge_key": found_lock["bridge_key"],
        "lock_key_local_id": found_lock["local_id"],
        "bridge_mdns_hostname": found_lock["bridge_hostname"],
        "bridge_ip": found_lock["bridge_ip"],
        "name": found_lock["name"],
        CONF_WEBHOOK_ID: webhook_id,
        CONF_API_TOKEN: "eyadiuyfasiuasf",
    })
    mock_lock.getWebhooks.assert_awaited()


@test
async def create_entry_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test we can create a lock via manual entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"] is None).to_be(True)

    lock_result = json.loads(await async_load_fixture(hass, "status_ok.json", DOMAIN))
    mock_lock = Mock(spec=loqed.Lock, id="Foo")
    webhook_id = "Webhook_ID"
    all_locks_response = json.loads(
        await async_load_fixture(hass, "get_all_locks.json", DOMAIN)
    )
    found_lock = all_locks_response["data"][0]

    with (
        patch(
            "loqedAPI.cloud_loqed.LoqedCloudAPI.async_get_locks",
            return_value=all_locks_response,
        ),
        patch(
            "loqedAPI.loqed.LoqedAPI.async_get_lock",
            return_value=mock_lock,
        ),
        patch(
            "homeassistant.components.loqed.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.webhook.async_generate_id",
            return_value=webhook_id,
        ),
        patch(
            "loqedAPI.loqed.LoqedAPI.async_get_lock_details", return_value=lock_result
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_TOKEN: "eyadiuyfasiuasf", CONF_NAME: "MyLock"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("LOQED Touch Smart Lock")
    expect(result2["data"]).to_equal({
        "id": "Foo",
        "lock_key_key": found_lock["key_secret"],
        "bridge_key": found_lock["bridge_key"],
        "lock_key_local_id": found_lock["local_id"],
        "bridge_mdns_hostname": found_lock["bridge_hostname"],
        "bridge_ip": found_lock["bridge_ip"],
        "name": found_lock["name"],
        CONF_WEBHOOK_ID: webhook_id,
        CONF_API_TOKEN: "eyadiuyfasiuasf",
    })
    mock_lock.getWebhooks.assert_awaited()


@test
async def cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"] is None).to_be(True)

    with patch(
        "loqedAPI.cloud_loqed.LoqedCloudAPI.async_get_locks",
        side_effect=aiohttp.ClientError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_TOKEN: "eyadiuyfasiuasf", CONF_NAME: "MyLock"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def invalid_auth_when_lock_not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test we handle a situation where the user enters an invalid lock name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"] is None).to_be(True)

    all_locks_response = json.loads(
        await async_load_fixture(hass, "get_all_locks.json", DOMAIN)
    )

    with patch(
        "loqedAPI.cloud_loqed.LoqedCloudAPI.async_get_locks",
        return_value=all_locks_response,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_TOKEN: "eyadiuyfasiuasf", CONF_NAME: "MyLock2"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def cannot_connect_when_lock_not_reachable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test we handle a situation where the user enters an invalid lock name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"] is None).to_be(True)

    all_locks_response = json.loads(
        await async_load_fixture(hass, "get_all_locks.json", DOMAIN)
    )

    with (
        patch(
            "loqedAPI.cloud_loqed.LoqedCloudAPI.async_get_locks",
            return_value=all_locks_response,
        ),
        patch(
            "loqedAPI.loqed.LoqedAPI.async_get_lock", side_effect=aiohttp.ClientError
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_TOKEN: "eyadiuyfasiuasf", CONF_NAME: "MyLock"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
