"""Test the Network UPS Tools (NUT) config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import patch

from aionut import NUTError, NUTLoginError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nut.config_flow import PASSWORD_NOT_CHANGED
from homeassistant.components.nut.const import DOMAIN
from homeassistant.const import (
    CONF_ALIAS,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_RESOURCES,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from .util import _get_mock_nutclient, async_init_integration

VALID_CONFIG = {
    CONF_HOST: "localhost",
    CONF_PORT: 123,
    CONF_NAME: "name",
    CONF_RESOURCES: ["battery.charge"],
}


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form_zeroconf(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we can setup from zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.5"),
            ip_addresses=[ip_address("192.168.1.5")],
            hostname="mock_hostname",
            name="mock_name",
            port=1234,
            properties={},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("192.168.1.5:1234")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.5",
            CONF_PASSWORD: "test-password",
            CONF_PORT: 1234,
            CONF_USERNAME: "test-username",
        }
    )
    expect(result2["result"].unique_id).to_be(None)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_user_one_alias(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we can configure a device with one alias."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.1.1.1:2222")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_PORT: 2222,
            CONF_USERNAME: "test-username",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_user_multiple_aliases(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can configure device with multiple aliases."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "2.2.2.2", CONF_PORT: 123, CONF_RESOURCES: ["battery.charge"]},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage"},
        list_ups={"ups1": "UPS 1", "ups2": "UPS2"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )

    expect(result2["step_id"]).to_equal("ups")
    expect(result2["type"]).to_be(FlowResultType.FORM)

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: "ups2"},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("ups2@1.1.1.1:2222")
    expect(result3["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_ALIAS: "ups2",
            CONF_PORT: 2222,
            CONF_USERNAME: "test-username",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(2)


@test
async def form_user_one_alias_with_ignored_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup a new one when there is an ignored one."""
    ignored_entry = MockConfigEntry(
        domain=DOMAIN, data={}, source=config_entries.SOURCE_IGNORE
    )
    ignored_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.1.1.1:2222")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_PORT: 2222,
            CONF_USERNAME: "test-username",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_no_aliases_found(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we abort when the NUT server has no aliases."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_pynut = _get_mock_nutclient()

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("no_ups_found")


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient.list_ups",
            side_effect=NUTError("no route to host"),
        ),
        patch(
            "homeassistant.components.nut.AIONUTClient.list_vars",
            side_effect=NUTError("no route to host"),
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
    expect(result2["description_placeholders"]).to_equal({"error": "no route to host"})

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient.list_ups",
            return_value={"ups1"},
        ),
        patch(
            "homeassistant.components.nut.AIONUTClient.list_vars",
            side_effect=Exception,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )
    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.1.1.1:2222")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_PORT: 2222,
            CONF_USERNAME: "test-username",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def auth_failures(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test authentication failures."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient.list_ups",
            side_effect=NUTLoginError,
        ),
        patch(
            "homeassistant.components.nut.AIONUTClient.list_vars",
            side_effect=NUTLoginError,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"password": "invalid_auth"})

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )
    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.1.1.1:2222")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_PORT: 2222,
            CONF_USERNAME: "test-username",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def reauth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauth flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 123,
            CONF_RESOURCES: ["battery.voltage"],
        },
    )
    config_entry.add_to_hass(hass)
    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    expect(len(flows)).to_equal(1)
    flow = flows[0]

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient.list_ups",
            side_effect=NUTLoginError,
        ),
        patch(
            "homeassistant.components.nut.AIONUTClient.list_vars",
            side_effect=NUTLoginError,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"password": "invalid_auth"})

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )
    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def abort_if_already_setup(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we abort if component is already setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 123,
            CONF_RESOURCES: ["battery.voltage"],
        },
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage"},
        list_ups={"ups1": "UPS 1"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 123,
            },
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("already_configured")


@test
async def abort_duplicate_unique_ids(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if unique_id is already setup."""
    list_vars = {
        "device.mfr": "Some manufacturer",
        "device.model": "Some model",
        "device.serial": "0000-1",
    }
    await async_init_integration(
        hass,
        list_ups={"ups1": "UPS 1"},
        list_vars=list_vars,
    )

    mock_pynut = _get_mock_nutclient(list_ups={"ups2": "UPS 2"}, list_vars=list_vars)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 2222,
            },
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("already_configured")


@test
async def abort_multiple_aliases_duplicate_unique_ids(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort on multiple aliases if unique_id is already setup."""
    list_vars = {
        "device.mfr": "Some manufacturer",
        "device.model": "Some model",
        "device.serial": "0000-1",
    }

    mock_pynut = _get_mock_nutclient(
        list_ups={"ups2": "UPS 2", "ups3": "UPS 3"}, list_vars=list_vars
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 2222,
            },
        )
        await hass.async_block_till_done()

        expect(result2["step_id"]).to_equal("ups")
        expect(result2["type"]).to_be(FlowResultType.FORM)

    await async_init_integration(
        hass,
        list_ups={"ups1": "UPS 1"},
        list_vars=list_vars,
    )

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ALIAS: "ups2"},
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("already_configured")


@test
async def abort_if_already_setup_alias(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if component is already setup with same alias."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 123,
            CONF_RESOURCES: ["battery.voltage"],
            CONF_ALIAS: "ups1",
        },
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage"},
        list_ups={"ups1": "UPS 1", "ups2": "UPS 2"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 123,
            },
        )

    expect(result2["step_id"]).to_equal("ups")
    expect(result2["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: "ups1"},
        )

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("already_configured")


@test
async def reconfigure_one_alias_successful(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure one alias successful."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage"},
        list_ups={"ups1": "UPS 1"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "2.2.2.2",
                CONF_PORT: 456,
                CONF_USERNAME: "test-new-username",
                CONF_PASSWORD: "test-new-password",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reconfigure_successful")

        expect(entry.data[CONF_HOST]).to_equal("2.2.2.2")
        expect(entry.data[CONF_PORT]).to_equal(456)
        expect(entry.data[CONF_USERNAME]).to_equal("test-new-username")
        expect(entry.data[CONF_PASSWORD]).to_equal("test-new-password")


@test
async def reconfigure_one_alias_nochange(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure one alias when there is no change."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: entry.data[CONF_HOST],
                CONF_PORT: int(entry.data[CONF_PORT]),
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: entry.data[CONF_PASSWORD],
            },
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reconfigure_successful")

        expect(entry.data[CONF_HOST]).to_equal("1.1.1.1")
        expect(entry.data[CONF_PORT]).to_equal(123)
        expect(entry.data[CONF_USERNAME]).to_equal("test-username")
        expect(entry.data[CONF_PASSWORD]).to_equal("test-password")


@test
async def reconfigure_one_alias_password_nochange(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure one alias when there is no password change."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage"},
        list_ups={"ups1": "UPS 1"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "2.2.2.2",
                CONF_PORT: 456,
                CONF_USERNAME: "test-new-username",
                CONF_PASSWORD: PASSWORD_NOT_CHANGED,
            },
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reconfigure_successful")

        expect(entry.data[CONF_HOST]).to_equal("2.2.2.2")
        expect(entry.data[CONF_PORT]).to_equal(456)
        expect(entry.data[CONF_USERNAME]).to_equal("test-new-username")
        expect(entry.data[CONF_PASSWORD]).to_equal("test-password")


@test
async def reconfigure_one_alias_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure when config changed to an existing host/port/alias."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    entry2 = await async_init_integration(
        hass,
        host="2.2.2.2",
        port=456,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry2.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: entry.data[CONF_HOST],
                CONF_PORT: int(entry.data[CONF_PORT]),
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: entry.data[CONF_PASSWORD],
            },
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("already_configured")

        expect(entry.data[CONF_HOST]).to_equal("1.1.1.1")
        expect(entry.data[CONF_PORT]).to_equal(123)
        expect(entry.data[CONF_USERNAME]).to_equal("test-username")
        expect(entry.data[CONF_PASSWORD]).to_equal("test-password")

        expect(entry2.data[CONF_HOST]).to_equal("2.2.2.2")
        expect(entry2.data[CONF_PORT]).to_equal(456)
        expect(entry2.data[CONF_USERNAME]).to_equal("test-username")
        expect(entry2.data[CONF_PASSWORD]).to_equal("test-password")


@test
async def reconfigure_one_alias_unique_id_change(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure when the unique ID is changed."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={
            "device.mfr": "Some manufacturer",
            "device.model": "Some model",
            "device.serial": "0000-1",
        },
    )

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={"ups1": "UPS 1"},
        list_vars={
            "device.mfr": "Another manufacturer",
            "device.model": "Another model",
            "device.serial": "0000-2",
        },
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: entry.data[CONF_HOST],
                CONF_PORT: entry.data[CONF_PORT],
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: entry.data[CONF_PASSWORD],
            },
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("unique_id_mismatch")


@test
async def reconfigure_one_alias_duplicate_unique_ids(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure that results in a duplicate unique ID."""
    list_vars = {
        "device.mfr": "Some manufacturer",
        "device.model": "Some model",
        "device.serial": "0000-1",
    }

    await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars=list_vars,
    )

    entry2 = await async_init_integration(
        hass,
        host="2.2.2.2",
        port=456,
        username="test-username",
        password="test-password",
        list_ups={"ups2": "UPS 2"},
        list_vars={
            "device.mfr": "Another manufacturer",
            "device.model": "Another model",
            "device.serial": "0000-2",
        },
    )

    result = await entry2.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={"ups2": "UPS 2"},
        list_vars=list_vars,
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "3.3.3.3",
                CONF_PORT: 789,
                CONF_USERNAME: "test-new-username",
                CONF_PASSWORD: "test-new-password",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("unique_id_mismatch")


@test
async def reconfigure_multiple_aliases_successful(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure with multiple aliases is successful."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={
            "ups1": "UPS 1",
            "ups2": "UPS 2",
        },
        list_vars={"battery.voltage": "voltage"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "2.2.2.2",
                CONF_PORT: 456,
                CONF_USERNAME: "test-new-username",
                CONF_PASSWORD: "test-new-password",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reconfigure_ups")

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: "ups2"},
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("reconfigure_successful")

        expect(entry.data[CONF_HOST]).to_equal("2.2.2.2")
        expect(entry.data[CONF_PORT]).to_equal(456)
        expect(entry.data[CONF_USERNAME]).to_equal("test-new-username")
        expect(entry.data[CONF_PASSWORD]).to_equal("test-new-password")
        expect(entry.data[CONF_ALIAS]).to_equal("ups2")


@test
async def reconfigure_multiple_aliases_nochange(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure with multiple aliases and no change."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={
            "ups1": "UPS 1",
            "ups2": "UPS 2",
        },
        list_vars={"battery.voltage": "voltage"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: entry.data[CONF_HOST],
                CONF_PORT: entry.data[CONF_PORT],
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: entry.data[CONF_PASSWORD],
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reconfigure_ups")

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: "ups1"},
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("reconfigure_successful")

        expect(entry.data[CONF_HOST]).to_equal("1.1.1.1")
        expect(entry.data[CONF_PORT]).to_equal(123)
        expect(entry.data[CONF_USERNAME]).to_equal("test-username")
        expect(entry.data[CONF_PASSWORD]).to_equal("test-password")
        expect(entry.data[CONF_ALIAS]).to_equal("ups1")


@test
async def reconfigure_multiple_aliases_password_nochange(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure with multiple aliases when no password change."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={
            "ups1": "UPS 1",
            "ups2": "UPS 2",
        },
        list_vars={"battery.voltage": "voltage"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "2.2.2.2",
                CONF_PORT: 456,
                CONF_USERNAME: "test-new-username",
                CONF_PASSWORD: PASSWORD_NOT_CHANGED,
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reconfigure_ups")

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: "ups2"},
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("reconfigure_successful")

        expect(entry.data[CONF_HOST]).to_equal("2.2.2.2")
        expect(entry.data[CONF_PORT]).to_equal(456)
        expect(entry.data[CONF_USERNAME]).to_equal("test-new-username")
        expect(entry.data[CONF_PASSWORD]).to_equal("test-password")
        expect(entry.data[CONF_ALIAS]).to_equal("ups2")


@test
async def reconfigure_multiple_aliases_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure multi aliases changed to existing host/port/alias."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        alias="ups1",
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1", "ups2": "UPS 2"},
        list_vars={"battery.voltage": "voltage"},
    )

    entry2 = await async_init_integration(
        hass,
        host="2.2.2.2",
        port=456,
        alias="ups2",
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={"battery.voltage": "voltage"},
    )

    expect(entry2.data[CONF_HOST]).to_equal("2.2.2.2")
    expect(entry2.data[CONF_PORT]).to_equal(456)
    expect(entry2.data[CONF_USERNAME]).to_equal("test-username")
    expect(entry2.data[CONF_PASSWORD]).to_equal("test-password")

    result = await entry2.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={
            "ups1": "UPS 1",
            "ups2": "UPS 2",
        },
        list_vars={"battery.voltage": "voltage"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: entry.data[CONF_HOST],
                CONF_PORT: entry.data[CONF_PORT],
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: entry.data[CONF_PASSWORD],
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reconfigure_ups")

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: entry.data[CONF_ALIAS]},
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("already_configured")

        expect(entry.data[CONF_HOST]).to_equal("1.1.1.1")
        expect(entry.data[CONF_PORT]).to_equal(123)
        expect(entry.data[CONF_USERNAME]).to_equal("test-username")
        expect(entry.data[CONF_PASSWORD]).to_equal("test-password")
        expect(entry.data[CONF_ALIAS]).to_equal("ups1")

        expect(entry2.data[CONF_HOST]).to_equal("2.2.2.2")
        expect(entry2.data[CONF_PORT]).to_equal(456)
        expect(entry2.data[CONF_USERNAME]).to_equal("test-username")
        expect(entry2.data[CONF_PASSWORD]).to_equal("test-password")
        expect(entry2.data[CONF_ALIAS]).to_equal("ups2")


@test
async def reconfigure_multiple_aliases_unique_id_change(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure with multiple aliases and the unique ID is changed."""
    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        alias="ups1",
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1", "ups2": "UPS 2"},
        list_vars={"battery.voltage": "voltage"},
    )

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={
            "ups1": "UPS 1",
            "ups2": "UPS 2",
        },
        list_vars={
            "device.mfr": "Another manufacturer",
            "device.model": "Another model",
            "device.serial": "0000-2",
        },
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: entry.data[CONF_HOST],
                CONF_PORT: entry.data[CONF_PORT],
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: entry.data[CONF_PASSWORD],
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reconfigure_ups")

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: entry.data[CONF_ALIAS]},
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("unique_id_mismatch")


@test
async def reconfigure_multiple_aliases_duplicate_unique_ids(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure multi aliases that results in duplicate unique ID."""
    list_vars = {
        "device.mfr": "Some manufacturer",
        "device.model": "Some model",
        "device.serial": "0000-1",
    }

    entry = await async_init_integration(
        hass,
        host="1.1.1.1",
        port=123,
        alias="ups1",
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1", "ups2": "UPS 2"},
        list_vars=list_vars,
    )

    entry2 = await async_init_integration(
        hass,
        host="2.2.2.2",
        port=456,
        alias="ups2",
        username="test-username",
        password="test-password",
        list_ups={"ups1": "UPS 1"},
        list_vars={
            "device.mfr": "Another manufacturer",
            "device.model": "Another model",
            "device.serial": "0000-2",
        },
    )

    result = await entry2.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_pynut = _get_mock_nutclient(
        list_ups={
            "ups1": "UPS 1",
            "ups2": "UPS 2",
        },
        list_vars=list_vars,
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "3.3.3.3",
                CONF_PORT: 789,
                CONF_USERNAME: "test-new-username",
                CONF_PASSWORD: "test-new-password",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reconfigure_ups")

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: entry.data[CONF_ALIAS]},
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.ABORT)
        expect(result3["reason"]).to_equal("unique_id_mismatch")
