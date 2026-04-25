"""Test the IDrive e2 config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from botocore.exceptions import EndpointConnectionError
from idrive_e2 import CannotConnect, InvalidAuth
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.idrive_e2 import ClientError
from homeassistant.components.idrive_e2.config_flow import CONF_ACCESS_KEY_ID
from homeassistant.components.idrive_e2.const import (
    CONF_BUCKET,
    CONF_ENDPOINT_URL,
    CONF_SECRET_ACCESS_KEY,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.selector import SelectSelector

from ._fixtures import mock_client, mock_config_entry, mock_idrive_client
from .const import USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _client: AsyncMock = Depends(mock_client),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _idrive: AsyncMock = Depends(mock_idrive_client),
    _client: AsyncMock = Depends(mock_client),
) -> None:
    """Test config flow success path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bucket")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_BUCKET: USER_INPUT[CONF_BUCKET]},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(USER_INPUT)


@test.cases(
    test.case(
        "invalid_credentials",
        exception=ClientError(
            {"Error": {"Code": "403", "Message": "Forbidden"}}, "list_buckets"
        ),
        errors={"base": "invalid_credentials"},
    ),
    test.case(
        "invalid_endpoint_url",
        exception=ValueError(),
        errors={"base": "invalid_endpoint_url"},
    ),
    test.case(
        "cannot_connect",
        exception=EndpointConnectionError(endpoint_url="http://example.com"),
        errors={"base": "cannot_connect"},
    ),
)
async def flow_list_buckets_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _idrive: AsyncMock = Depends(mock_idrive_client),
    client: AsyncMock = Depends(mock_client),
    *,
    exception: Exception,
    errors: dict[str, str],
) -> None:
    """Test errors when listing buckets."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    client.list_buckets.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal(errors)

    client.list_buckets.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bucket")

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {CONF_BUCKET: USER_INPUT[CONF_BUCKET]},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(USER_INPUT)


@test
async def flow_no_buckets(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _idrive: AsyncMock = Depends(mock_idrive_client),
    client: AsyncMock = Depends(mock_client),
) -> None:
    """Test we show an error when no buckets are returned."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    client.list_buckets.return_value = {"Buckets": []}
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "no_buckets"})

    client.list_buckets.return_value = {"Buckets": [{"Name": USER_INPUT[CONF_BUCKET]}]}
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bucket")

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {CONF_BUCKET: USER_INPUT[CONF_BUCKET]},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(USER_INPUT)


@test
async def flow_bucket_step_options_from_s3_list_buckets(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _idrive: AsyncMock = Depends(mock_idrive_client),
    client: AsyncMock = Depends(mock_client),
) -> None:
    """Test bucket step shows dropdown options coming from S3 list_buckets()."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    client.list_buckets.return_value = {
        "Buckets": [{"Name": "bucket1"}, {"Name": "bucket2"}]
    }

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bucket")

    schema = result["data_schema"].schema
    selector = schema[vol.Required(CONF_BUCKET)]
    expect(isinstance(selector, SelectSelector)).to_be(True)

    cfg = selector.config
    options = cfg["options"] if isinstance(cfg, dict) else cfg.options

    expect(options).to_equal(["bucket1", "bucket2"])

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {CONF_BUCKET: "bucket1"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("bucket1")
    expect(result["data"][CONF_BUCKET]).to_equal("bucket1")


@test.cases(
    test.case(
        "invalid_credentials",
        exception=InvalidAuth("Invalid credentials"),
        expected_error="invalid_credentials",
    ),
    test.case(
        "cannot_connect",
        exception=CannotConnect("cannot connect"),
        expected_error="cannot_connect",
    ),
)
async def flow_get_region_endpoint_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    idrive: AsyncMock = Depends(mock_idrive_client),
    _client: AsyncMock = Depends(mock_client),
    *,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test user step error mapping when resolving region endpoint via client."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    idrive.get_region_endpoint.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})

    idrive.get_region_endpoint.side_effect = None
    idrive.get_region_endpoint.return_value = USER_INPUT[CONF_ENDPOINT_URL]

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bucket")

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {CONF_BUCKET: USER_INPUT[CONF_BUCKET]},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(USER_INPUT)


@test
async def abort_if_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _idrive: AsyncMock = Depends(mock_idrive_client),
    _client: AsyncMock = Depends(mock_client),
) -> None:
    """Test we abort if the account is already configured."""
    MockConfigEntry(
        domain=config_entry.domain,
        title=config_entry.title,
        data={
            **config_entry.data,
            CONF_BUCKET: USER_INPUT[CONF_BUCKET],
            CONF_ENDPOINT_URL: USER_INPUT[CONF_ENDPOINT_URL],
        },
        unique_id="existing",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bucket")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_BUCKET: USER_INPUT[CONF_BUCKET]},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
