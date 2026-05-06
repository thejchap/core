"""Test the lg_soundbar config flow."""

from __future__ import annotations

from collections.abc import Callable
import socket
from typing import Any
from unittest.mock import DEFAULT, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.lg_soundbar.const import DEFAULT_PORT, DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def setup_mock_temescal(
    hass: HomeAssistant,
    mock_temescal: MagicMock,
    mac_info_dev: dict[str, Any] | None = None,
    product_info: dict[str, Any] | None = None,
    info: dict[str, Any] | None = None,
) -> None:
    """Set up a mock of the temescal object to craft our expected responses."""
    tmock = mock_temescal.temescal
    instance = tmock.return_value

    def create_temescal_response(msg: str, data: dict | None = None) -> dict[str, Any]:
        response: dict[str, Any] = {"msg": msg}
        if data is not None:
            response["data"] = data
        return response

    def temescal_side_effect(
        addr: str, port: int, callback: Callable[[dict[str, Any]], None]
    ):
        mac_info_response = create_temescal_response(
            msg="MAC_INFO_DEV", data=mac_info_dev
        )
        product_info_response = create_temescal_response(
            msg="PRODUCT_INFO", data=product_info
        )
        info_response = create_temescal_response(msg="SPK_LIST_VIEW_INFO", data=info)

        instance.get_mac_info.side_effect = lambda: hass.add_job(
            callback, mac_info_response
        )
        instance.get_product_info.side_effect = lambda: hass.add_job(
            callback, product_info_response
        )
        instance.get_info.side_effect = lambda: hass.add_job(callback, info_response)

        return DEFAULT

    tmock.side_effect = temescal_side_effect


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
            "homeassistant.components.lg_soundbar.config_flow.temescal"
        ) as mock_temescal,
        patch(
            "homeassistant.components.lg_soundbar.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        setup_mock_temescal(
            hass=hass,
            mock_temescal=mock_temescal,
            mac_info_dev={"s_uuid": "uuid"},
            info={"s_user_name": "name"},
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("name")
    expect(result2["result"].unique_id).to_equal("uuid")
    expect(result2["data"]).to_equal({CONF_HOST: "1.1.1.1", CONF_PORT: DEFAULT_PORT})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_mac_info_response_empty(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form, but response from the initial get_mac_info function call is empty."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.lg_soundbar.config_flow.temescal"
        ) as mock_temescal,
        patch(
            "homeassistant.components.lg_soundbar.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        setup_mock_temescal(
            hass=hass,
            mock_temescal=mock_temescal,
            mac_info_dev={"s_uuid": "uuid"},
            info={"s_user_name": "name"},
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("name")
    expect(result2["result"].unique_id).to_equal("uuid")
    expect(result2["data"]).to_equal({CONF_HOST: "1.1.1.1", CONF_PORT: DEFAULT_PORT})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_uuid_present_in_both_functions_uuid_q_empty(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Get the form, uuid present in both get_mac_info and get_product_info calls."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.lg_soundbar.config_flow.temescal"
        ) as mock_temescal,
        patch(
            "homeassistant.components.lg_soundbar.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        setup_mock_temescal(
            hass=hass,
            mock_temescal=mock_temescal,
            mac_info_dev={"s_uuid": "uuid"},
            product_info={"s_uuid": "uuid"},
            info={"s_user_name": "name"},
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("name")
    expect(result2["result"].unique_id).to_equal("uuid")
    expect(result2["data"]).to_equal({CONF_HOST: "1.1.1.1", CONF_PORT: DEFAULT_PORT})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_uuid_present_in_both_functions_uuid_q_not_empty(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Get the form, uuid present in both get_mac_info and get_product_info calls."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.lg_soundbar.config_flow.QUEUE_TIMEOUT",
            new=0.1,
        ),
        patch(
            "homeassistant.components.lg_soundbar.config_flow.temescal"
        ) as mock_temescal,
        patch(
            "homeassistant.components.lg_soundbar.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        setup_mock_temescal(
            hass=hass,
            mock_temescal=mock_temescal,
            mac_info_dev={"s_uuid": "uuid"},
            product_info={"s_uuid": "uuid"},
            info={"s_user_name": "name"},
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("name")
    expect(result2["result"].unique_id).to_equal("uuid")
    expect(result2["data"]).to_equal({CONF_HOST: "1.1.1.1", CONF_PORT: DEFAULT_PORT})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_uuid_missing_from_mac_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form, but uuid is missing from the initial get_mac_info function call."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.lg_soundbar.config_flow.temescal"
        ) as mock_temescal,
        patch(
            "homeassistant.components.lg_soundbar.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        setup_mock_temescal(
            hass=hass,
            mock_temescal=mock_temescal,
            product_info={"s_uuid": "uuid"},
            info={"s_user_name": "name"},
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("name")
    expect(result2["result"].unique_id).to_equal("uuid")
    expect(result2["data"]).to_equal({CONF_HOST: "1.1.1.1", CONF_PORT: DEFAULT_PORT})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_uuid_not_provided_by_api(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form, but uuid is missing from the all API messages."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.lg_soundbar.config_flow.QUEUE_TIMEOUT",
            new=0.1,
        ),
        patch(
            "homeassistant.components.lg_soundbar.config_flow.temescal"
        ) as mock_temescal,
        patch(
            "homeassistant.components.lg_soundbar.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        setup_mock_temescal(
            hass=hass,
            mock_temescal=mock_temescal,
            product_info={"i_model_no": "8", "i_model_type": 0},
            info={"s_user_name": "name"},
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("name")
    expect(result2["result"].unique_id).to_be(None)
    expect(result2["data"]).to_equal({CONF_HOST: "1.1.1.1", CONF_PORT: DEFAULT_PORT})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_both_queues_empty(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form, but none of the data we want is provided by the API."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.lg_soundbar.config_flow.QUEUE_TIMEOUT",
            new=0.1,
        ),
        patch(
            "homeassistant.components.lg_soundbar.config_flow.temescal"
        ) as mock_temescal,
        patch(
            "homeassistant.components.lg_soundbar.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        setup_mock_temescal(hass=hass, mock_temescal=mock_temescal)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "no_data"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def no_uuid_host_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle if the device has no UUID and the host has already been configured."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PORT: DEFAULT_PORT,
        },
    )
    mock_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.lg_soundbar.config_flow.QUEUE_TIMEOUT",
            new=0.1,
        ),
        patch(
            "homeassistant.components.lg_soundbar.config_flow.temescal"
        ) as mock_temescal,
    ):
        setup_mock_temescal(
            hass=hass, mock_temescal=mock_temescal, info={"s_user_name": "name"}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def form_socket_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle socket.timeout error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.lg_soundbar.config_flow.temescal"
    ) as mock_temescal:
        mock_temescal.temescal.side_effect = socket.timeout
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_os_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle OSError."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.lg_soundbar.config_flow.temescal"
    ) as mock_temescal:
        mock_temescal.temescal.side_effect = OSError
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle already configured error."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 0,
        },
        unique_id="uuid",
    )
    mock_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.lg_soundbar.config_flow.temescal"
    ) as mock_temescal:
        setup_mock_temescal(
            hass=hass,
            mock_temescal=mock_temescal,
            mac_info_dev={"s_uuid": "uuid"},
            info={"s_user_name": "name"},
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
