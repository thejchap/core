"""Test the huum config flow."""

from unittest.mock import AsyncMock

from huum.exceptions import Forbidden
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.huum.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_huum_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_USERNAME = "huum@sauna.org"
TEST_PASSWORD = "ukuuku"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _huum: AsyncMock = Depends(mock_huum_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_USERNAME)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def signup_flow_already_set_up(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _huum: AsyncMock = Depends(mock_huum_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that we handle already existing entities with same id."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test.cases(
    test.case("unknown", raises=Exception, error_base="unknown"),
    test.case("invalid_auth", raises=Forbidden, error_base="invalid_auth"),
)
async def huum_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    huum: AsyncMock = Depends(mock_huum_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    raises: type[Exception],
    error_base: str,
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    huum.status.side_effect = raises
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    huum.status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _huum: AsyncMock = Depends(mock_huum_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication flow succeeds with valid credentials."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_password"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_USERNAME]).to_equal(TEST_USERNAME)
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_password")


@test.cases(
    test.case("unknown", raises=Exception, error_base="unknown"),
    test.case("invalid_auth", raises=Forbidden, error_base="invalid_auth"),
)
async def reauth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    huum: AsyncMock = Depends(mock_huum_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    raises: type[Exception],
    error_base: str,
) -> None:
    """Test reauthentication flow handles errors and recovers."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    huum.status.side_effect = raises
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "wrong_password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    # Recover with valid credentials.
    huum.status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_password"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_USERNAME]).to_equal(TEST_USERNAME)
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_password")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _huum: AsyncMock = Depends(mock_huum_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "new@sauna.org",
            CONF_PASSWORD: "new_password",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.title).to_equal("new@sauna.org")
    expect(config_entry.data[CONF_USERNAME]).to_equal("new@sauna.org")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_password")


@test
async def reconfigure_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _huum: AsyncMock = Depends(mock_huum_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration flow aborts when username already configured."""
    config_entry.add_to_hass(hass)

    other_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "other@sauna.org",
            CONF_PASSWORD: "other_password",
        },
        entry_id="OTHER_ENTRY",
    )
    other_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "other@sauna.org",
            CONF_PASSWORD: "new_password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("unknown", raises=Exception, error_base="unknown"),
    test.case("invalid_auth", raises=Forbidden, error_base="invalid_auth"),
)
async def reconfigure_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    huum: AsyncMock = Depends(mock_huum_client),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    raises: type[Exception],
    error_base: str,
) -> None:
    """Test reconfiguration flow handles errors and recovers."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    huum.status.side_effect = raises
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: "wrong_password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    # Recover with valid credentials.
    huum.status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: "new_password",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_USERNAME]).to_equal(TEST_USERNAME)
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_password")
