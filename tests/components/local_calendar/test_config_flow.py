"""Test the Local Calendar config flow."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.local_calendar.const import (
    ATTR_CREATE_EMPTY,
    ATTR_IMPORT_ICS_FILE,
    CONF_CALENDAR_NAME,
    CONF_ICS_FILE,
    CONF_IMPORT,
    CONF_STORAGE_KEY,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    config_entry,
    mock_process_uploaded_file,
    mock_process_uploaded_file_invalid,
    set_time_zone,
    setup_integration,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _tz: None = Depends(set_time_zone),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


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
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.local_calendar.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CALENDAR_NAME: "My Calendar",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("My Calendar")
    expect(result2["data"]).to_equal(
        {
            CONF_CALENDAR_NAME: "My Calendar",
            CONF_IMPORT: ATTR_CREATE_EMPTY,
            CONF_STORAGE_KEY: "my_calendar",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_import_ics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    upload: MagicMock = Depends(mock_process_uploaded_file),
) -> None:
    """Test we get the import form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CALENDAR_NAME: "My Calendar", CONF_IMPORT: ATTR_IMPORT_ICS_FILE},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.local_calendar.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        file_id = upload.file_id
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ICS_FILE: file_id[CONF_ICS_FILE]},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_integration),
    _entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test two calendars cannot be added with the same name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            # Pick a name that has the same slugify value as an existing config entry.
            CONF_CALENDAR_NAME: "light schedule",
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def invalid_ics(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    upload: MagicMock = Depends(mock_process_uploaded_file_invalid),
) -> None:
    """Test invalid ics content raises error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CALENDAR_NAME: "My Calendar", CONF_IMPORT: ATTR_IMPORT_ICS_FILE},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)

    file_id = upload.file_id
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ICS_FILE: file_id[CONF_ICS_FILE]},
    )
    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["errors"]).to_equal({CONF_ICS_FILE: "invalid_ics_file"})
