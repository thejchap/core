"""Test the Folder Watcher config flow."""

from pathlib import Path
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.folder_watcher.const import (
    CONF_FOLDER,
    CONF_PATTERNS,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    mock_network,
    tmp_path as tmp_path_fixture,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we get the form."""
    path = tmp_path.as_posix()
    hass.config.allowlist_external_dirs = {path}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_FOLDER: path},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Folder Watcher {path}")
    expect(result["options"]).to_equal({CONF_FOLDER: path, CONF_PATTERNS: ["*"]})


@test
async def form_not_allowed_path(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we handle not allowed path."""
    path = tmp_path.as_posix()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_FOLDER: path},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "not_allowed_dir"})

    hass.config.allowlist_external_dirs = {tmp_path}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_FOLDER: path},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Folder Watcher {path}")
    expect(result["options"]).to_equal({CONF_FOLDER: path, CONF_PATTERNS: ["*"]})


@test
async def form_not_directory(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we handle not a directory."""
    path = tmp_path.as_posix()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_FOLDER: "not_a_directory"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "not_dir"})

    hass.config.allowlist_external_dirs = {path}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_FOLDER: path},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Folder Watcher {path}")
    expect(result["options"]).to_equal({CONF_FOLDER: path, CONF_PATTERNS: ["*"]})


@test
async def form_not_readable_dir(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we handle not able to read directory."""
    path = tmp_path.as_posix()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("os.access", return_value=False):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_FOLDER: path},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "not_readable_dir"})

    hass.config.allowlist_external_dirs = {path}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_FOLDER: path},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Folder Watcher {path}")
    expect(result["options"]).to_equal({CONF_FOLDER: path, CONF_PATTERNS: ["*"]})


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we abort when entry is already configured."""
    path = tmp_path.as_posix()
    hass.config.allowlist_external_dirs = {path}

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=f"Folder Watcher {path}",
        data={CONF_FOLDER: path},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_FOLDER: path},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
