"""Tests for the Filesize config flow."""

from pathlib import Path
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.filesize.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_FILE_PATH
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import TEST_FILE_NAME, TEST_FILE_NAME2, async_create_file
from ._fixtures import mock_config_entry, mock_setup_entry

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
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test the full user configuration flow."""
    test_file = str(tmp_path.joinpath(TEST_FILE_NAME))
    await async_create_file(hass, test_file)
    hass.config.allowlist_external_dirs = {tmp_path}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_FILE_PATH: test_file},
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal(TEST_FILE_NAME)
    expect(result2.get("data")).to_equal({CONF_FILE_PATH: test_file})


@test
async def unique_path(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test we abort if already setup."""
    test_file = str(tmp_path.joinpath(TEST_FILE_NAME))
    await async_create_file(hass, test_file)
    hass.config.allowlist_external_dirs = {tmp_path}
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_FILE_PATH: test_file}
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def flow_fails_on_validation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test config flow errors."""
    test_file = str(tmp_path.joinpath(TEST_FILE_NAME))
    hass.config.allowlist_external_dirs = set()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_FILE_PATH: test_file,
        },
    )

    expect(result2["errors"]).to_equal({"base": "not_valid"})

    await async_create_file(hass, test_file)

    with patch(
        "homeassistant.components.filesize.config_flow.pathlib.Path",
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_FILE_PATH: test_file,
            },
        )

    expect(result2["errors"]).to_equal({"base": "not_allowed"})

    hass.config.allowlist_external_dirs = {tmp_path}
    with patch(
        "homeassistant.components.filesize.config_flow.pathlib.Path",
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_FILE_PATH: test_file,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_FILE_NAME)
    expect(result2["data"]).to_equal(
        {
            CONF_FILE_PATH: test_file,
        }
    )


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test a reconfigure flow."""
    test_file = str(tmp_path.joinpath(TEST_FILE_NAME2))
    await async_create_file(hass, test_file)
    hass.config.allowlist_external_dirs = {tmp_path}
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_FILE_PATH: test_file},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal({CONF_FILE_PATH: str(test_file)})


@test
async def unique_id_already_exist_in_reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test a reconfigure flow fails when unique id already exist."""
    test_file = str(tmp_path.joinpath(TEST_FILE_NAME))
    test_file2 = str(tmp_path.joinpath(TEST_FILE_NAME2))
    await async_create_file(hass, test_file)
    await async_create_file(hass, test_file2)
    hass.config.allowlist_external_dirs = {tmp_path}
    config_entry = MockConfigEntry(
        title=TEST_FILE_NAME,
        domain=DOMAIN,
        data={CONF_FILE_PATH: test_file},
        unique_id=test_file,
    )
    config_entry2 = MockConfigEntry(
        title=TEST_FILE_NAME2,
        domain=DOMAIN,
        data={CONF_FILE_PATH: test_file2},
        unique_id=test_file2,
    )
    config_entry.add_to_hass(hass)
    config_entry2.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_FILE_PATH: test_file2},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def reconfigure_flow_fails_on_validation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tmp_path: Path = Depends(tmp_path_fixture),
) -> None:
    """Test config flow errors in reconfigure."""
    test_file2 = str(tmp_path.joinpath(TEST_FILE_NAME2))
    hass.config.allowlist_external_dirs = set()

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_FILE_PATH: test_file2,
        },
    )

    expect(result["errors"]).to_equal({"base": "not_valid"})

    await async_create_file(hass, test_file2)

    with patch(
        "homeassistant.components.filesize.config_flow.pathlib.Path",
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_FILE_PATH: test_file2,
            },
        )

    expect(result2["errors"]).to_equal({"base": "not_allowed"})

    hass.config.allowlist_external_dirs = {tmp_path}
    with patch(
        "homeassistant.components.filesize.config_flow.pathlib.Path",
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_FILE_PATH: test_file2,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")
