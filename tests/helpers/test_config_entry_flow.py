"""Tests for the Config Entry Flow helper."""

import asyncio
from collections.abc import Callable, Generator
from contextlib import contextmanager
from unittest.mock import Mock, PropertyMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, data_entry_flow, setup
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.helpers import config_entry_flow

from tests.common import MockConfigEntry, MockModule, mock_integration, mock_platform
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@contextmanager
def _make_discovery_flow_conf(
    has_discovered_devices: Callable[[HomeAssistant], asyncio.Future[bool] | bool],
) -> Generator[None]:
    with patch.dict(config_entries.HANDLERS):
        config_entry_flow.register_discovery_flow(
            "test", "Test", has_discovered_devices
        )
        yield


@fixture
def discovery_flow_conf(
    hass: HomeAssistant = Depends(hass),
) -> Generator[dict[str, bool]]:
    """Register a handler with a async friendly callback function."""
    handler_conf = {"discovered": False}

    def has_discovered_devices(hass: HomeAssistant) -> bool:
        """Mock if we have discovered devices."""
        return handler_conf["discovered"]

    with _make_discovery_flow_conf(has_discovered_devices):
        yield handler_conf


@fixture
def webhook_flow_conf(hass: HomeAssistant = Depends(hass)) -> Generator[None]:
    """Register a handler."""
    with patch.dict(config_entries.HANDLERS):
        config_entry_flow.register_webhook_flow("test_single", "Test Single", {}, False)
        config_entry_flow.register_webhook_flow(
            "test_multiple", "Test Multiple", {}, True
        )
        yield


@test
async def single_entry_allowed(
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test only a single entry is allowed."""
    flow = config_entries.HANDLERS["test"]()
    flow.hass = hass
    flow.context = {}

    MockConfigEntry(domain="test").add_to_hass(hass)
    result = await flow.async_step_user()

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def user_no_devices_found(
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test if no devices found."""
    flow = config_entries.HANDLERS["test"]()
    flow.hass = hass
    flow.context = {"source": config_entries.SOURCE_USER}
    result = await flow.async_step_confirm(user_input={})

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_has_confirmation(
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test user requires confirmation to setup."""
    discovery_flow_conf["discovered"] = True
    mock_platform(hass, "test.config_flow", None)

    result = await hass.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_USER}, data={}
    )

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    progress = hass.config_entries.flow.async_progress()
    expect(len(progress)).to_equal(1)
    expect(progress[0]["flow_id"]).to_equal(result["flow_id"])
    expect(progress[0]["context"]).to_equal(
        {
            "confirm_only": True,
            "source": config_entries.SOURCE_USER,
            "unique_id": "test",
        }
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)


@test
async def user_has_confirmation_async_discovery_flow(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test user requires confirmation to setup with an async has_discovered_devices."""
    handler_conf = {"discovered": True}

    async def has_discovered_devices(hass: HomeAssistant) -> bool:
        """Mock if we have discovered devices."""
        return handler_conf["discovered"]

    with _make_discovery_flow_conf(has_discovered_devices):
        mock_platform(hass, "test.config_flow", None)

        result = await hass.config_entries.flow.async_init(
            "test", context={"source": config_entries.SOURCE_USER}, data={}
        )

        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
        expect(result["step_id"]).to_equal("confirm")

        progress = hass.config_entries.flow.async_progress()
        expect(len(progress)).to_equal(1)
        expect(progress[0]["flow_id"]).to_equal(result["flow_id"])
        expect(progress[0]["context"]).to_equal(
            {
                "confirm_only": True,
                "source": config_entries.SOURCE_USER,
                "unique_id": "test",
            }
        )

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("bluetooth", source=config_entries.SOURCE_BLUETOOTH),
    test.case("discovery", source=config_entries.SOURCE_DISCOVERY),
    test.case("mqtt", source=config_entries.SOURCE_MQTT),
    test.case("ssdp", source=config_entries.SOURCE_SSDP),
    test.case("zeroconf", source=config_entries.SOURCE_ZEROCONF),
    test.case("dhcp", source=config_entries.SOURCE_DHCP),
)
async def discovery_single_instance(
    source: str,
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test we not allow duplicates."""
    flow = config_entries.HANDLERS["test"]()
    flow.hass = hass
    flow.context = {}

    MockConfigEntry(domain="test").add_to_hass(hass)
    result = await getattr(flow, f"async_step_{source}")({})

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test.cases(
    test.case("bluetooth", source=config_entries.SOURCE_BLUETOOTH),
    test.case("discovery", source=config_entries.SOURCE_DISCOVERY),
    test.case("mqtt", source=config_entries.SOURCE_MQTT),
    test.case("ssdp", source=config_entries.SOURCE_SSDP),
    test.case("zeroconf", source=config_entries.SOURCE_ZEROCONF),
    test.case("dhcp", source=config_entries.SOURCE_DHCP),
)
async def discovery_confirmation(
    source: str,
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test we ask for confirmation via discovery."""
    flow = config_entries.HANDLERS["test"]()
    flow.hass = hass
    flow.context = {"source": source}

    result = await getattr(flow, f"async_step_{source}")({})

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await flow.async_step_confirm({})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("bluetooth", source=config_entries.SOURCE_BLUETOOTH),
    test.case("discovery", source=config_entries.SOURCE_DISCOVERY),
    test.case("mqtt", source=config_entries.SOURCE_MQTT),
    test.case("ssdp", source=config_entries.SOURCE_SSDP),
    test.case("zeroconf", source=config_entries.SOURCE_ZEROCONF),
    test.case("dhcp", source=config_entries.SOURCE_DHCP),
)
async def discovery_during_onboarding(
    source: str,
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test we create config entry via discovery during onboarding."""
    flow = config_entries.HANDLERS["test"]()
    flow.hass = hass
    flow.context = {"source": source}

    with patch(
        "homeassistant.components.onboarding.async_is_onboarded", return_value=False
    ):
        result = await getattr(flow, f"async_step_{source}")({})

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)


@test
async def multiple_discoveries(
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test we only create one instance for multiple discoveries."""
    mock_platform(hass, "test.config_flow", None)

    result = await hass.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    # Second discovery
    result = await hass.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)


@test
async def only_one_in_progress(
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test a user initialized one will finish and cancel discovered one."""
    mock_platform(hass, "test.config_flow", None)

    # Discovery starts flow
    result = await hass.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    # User starts flow
    result = await hass.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_USER}, data={}
    )

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    # Discovery flow has not been aborted
    expect(len(hass.config_entries.flow.async_progress())).to_equal(2)

    # Discovery should be aborted once user confirms
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(len(hass.config_entries.flow.async_progress())).to_equal(0)


@test
async def import_abort_discovery(
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test import will finish and cancel discovered one."""
    mock_platform(hass, "test.config_flow", None)

    # Discovery starts flow
    result = await hass.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    # Start import flow
    result = await hass.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_IMPORT}, data={}
    )

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)

    # Discovery flow has been aborted
    expect(len(hass.config_entries.flow.async_progress())).to_equal(0)


@test
async def import_no_confirmation(
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test import requires no confirmation to set up."""
    flow = config_entries.HANDLERS["test"]()
    flow.hass = hass
    flow.context = {}
    discovery_flow_conf["discovered"] = True

    result = await flow.async_step_import(None)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)


@test
async def import_single_instance(
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test import doesn't create second instance."""
    flow = config_entries.HANDLERS["test"]()
    flow.hass = hass
    flow.context = {}
    discovery_flow_conf["discovered"] = True
    MockConfigEntry(domain="test").add_to_hass(hass)

    result = await flow.async_step_import(None)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)


@test
async def ignored_discoveries(
    hass: HomeAssistant = Depends(hass),
    discovery_flow_conf: dict[str, bool] = Depends(discovery_flow_conf),
) -> None:
    """Test we can ignore discovered entries."""
    mock_platform(hass, "test.config_flow", None)

    result = await hass.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    flow = next(
        (
            flw
            for flw in hass.config_entries.flow.async_progress()
            if flw["flow_id"] == result["flow_id"]
        ),
        None,
    )

    # Ignore it.
    await hass.config_entries.flow.async_init(
        flow["handler"],
        context={"source": config_entries.SOURCE_IGNORE},
        data={"unique_id": flow["context"]["unique_id"], "title": "Ignored Entry"},
    )

    # Second discovery should be aborted
    result = await hass.config_entries.flow.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data={}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)


@test
async def webhook_single_entry_allowed(
    hass: HomeAssistant = Depends(hass),
    webhook_flow_conf: None = Depends(webhook_flow_conf),
) -> None:
    """Test only a single entry is allowed."""
    flow = config_entries.HANDLERS["test_single"]()
    flow.hass = hass

    MockConfigEntry(domain="test_single").add_to_hass(hass)
    result = await flow.async_step_user()

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def webhook_multiple_entries_allowed(
    hass: HomeAssistant = Depends(hass),
    webhook_flow_conf: None = Depends(webhook_flow_conf),
) -> None:
    """Test multiple entries are allowed when specified."""
    flow = config_entries.HANDLERS["test_multiple"]()
    flow.hass = hass

    MockConfigEntry(domain="test_multiple").add_to_hass(hass)
    hass.config.api = Mock(base_url="http://example.com")

    result = await flow.async_step_user()
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)


@test
async def webhook_config_flow_registers_webhook(
    hass: HomeAssistant = Depends(hass),
    webhook_flow_conf: None = Depends(webhook_flow_conf),
) -> None:
    """Test setting up an entry creates a webhook."""
    flow = config_entries.HANDLERS["test_single"]()
    flow.hass = hass

    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com"},
    )
    result = await flow.async_step_user(user_input={})

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]["webhook_id"]).not_.to_be_none()


@test
async def webhook_create_cloudhook(
    hass: HomeAssistant = Depends(hass),
    webhook_flow_conf: None = Depends(webhook_flow_conf),
) -> None:
    """Test cloudhook will be created if subscribed."""
    expect(await setup.async_setup_component(hass, "cloud", {})).to_be_truthy()

    async_setup_entry = Mock(return_value=True)
    async_unload_entry = Mock(return_value=True)

    mock_integration(
        hass,
        MockModule(
            "test_single",
            async_setup_entry=async_setup_entry,
            async_unload_entry=async_unload_entry,
            async_remove_entry=config_entry_flow.webhook_async_remove_entry,
        ),
    )
    mock_platform(hass, "test_single.config_flow", None)

    result = await hass.config_entries.flow.async_init(
        "test_single", context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    with (
        patch(
            "hass_nabucasa.cloudhooks.Cloudhooks.async_create",
            return_value={"cloudhook_url": "https://example.com"},
        ) as mock_create,
        patch(
            "hass_nabucasa.Cloud.subscription_expired",
            new_callable=PropertyMock(return_value=False),
        ),
        patch(
            "hass_nabucasa.Cloud.is_logged_in",
            new_callable=PropertyMock(return_value=True),
        ),
        patch(
            "hass_nabucasa.iot_base.BaseIoT.connected",
            new_callable=PropertyMock(return_value=True),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["description_placeholders"]["webhook_url"]).to_equal(
        "https://example.com"
    )
    expect(len(mock_create.mock_calls)).to_equal(1)
    expect(len(async_setup_entry.mock_calls)).to_equal(1)

    with patch(
        "hass_nabucasa.cloudhooks.Cloudhooks.async_delete",
        return_value={"cloudhook_url": "https://example.com"},
    ) as mock_delete:
        result = await hass.config_entries.async_remove(result["result"].entry_id)

    expect(len(mock_delete.mock_calls)).to_equal(1)
    expect(result["require_restart"]).to_be(False)
    await hass.async_block_till_done()


@test
async def webhook_create_cloudhook_aborts_not_connected(
    hass: HomeAssistant = Depends(hass),
    webhook_flow_conf: None = Depends(webhook_flow_conf),
) -> None:
    """Test cloudhook aborts if subscribed but not connected."""
    expect(await setup.async_setup_component(hass, "cloud", {})).to_be_truthy()

    async_setup_entry = Mock(return_value=True)
    async_unload_entry = Mock(return_value=True)

    mock_integration(
        hass,
        MockModule(
            "test_single",
            async_setup_entry=async_setup_entry,
            async_unload_entry=async_unload_entry,
            async_remove_entry=config_entry_flow.webhook_async_remove_entry,
        ),
    )
    mock_platform(hass, "test_single.config_flow", None)

    result = await hass.config_entries.flow.async_init(
        "test_single", context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    with (
        patch(
            "hass_nabucasa.cloudhooks.Cloudhooks.async_create",
            return_value={"cloudhook_url": "https://example.com"},
        ),
        patch(
            "hass_nabucasa.Cloud.subscription_expired",
            new_callable=PropertyMock(return_value=False),
        ),
        patch(
            "hass_nabucasa.Cloud.is_logged_in",
            new_callable=PropertyMock(return_value=True),
        ),
        patch(
            "hass_nabucasa.iot_base.BaseIoT.connected",
            new_callable=PropertyMock(return_value=False),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cloud_not_connected")


@test
async def webhook_reconfigure_flow(
    hass: HomeAssistant = Depends(hass),
    webhook_flow_conf: None = Depends(webhook_flow_conf),
) -> None:
    """Test webhook reconfigure flow."""
    config_entry = MockConfigEntry(
        domain="test_single",
        data={
            "webhook_id": "12345",
            "cloudhook": False,
            "other_entry_data": "not_changed",
        },
    )
    config_entry.add_to_hass(hass)

    flow = config_entries.HANDLERS["test_single"]()
    flow.hass = hass
    flow.context = {
        "source": config_entries.SOURCE_RECONFIGURE,
        "entry_id": config_entry.entry_id,
    }

    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com"},
    )

    result = await flow.async_step_reconfigure()
    expect(result["type"]).to_be(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await flow.async_step_reconfigure(user_input={})

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(result["description_placeholders"]).to_equal(
        {"webhook_url": "https://example.com/api/webhook/12345"}
    )
    expect(config_entry.data["webhook_id"]).to_equal("12345")
    expect(config_entry.data["cloudhook"]).to_be(False)
    expect(config_entry.data["other_entry_data"]).to_equal("not_changed")


@test
async def webhook_reconfigure_cloudhook(
    hass: HomeAssistant = Depends(hass),
    webhook_flow_conf: None = Depends(webhook_flow_conf),
) -> None:
    """Test reconfigure updates to cloudhook if subscribed."""
    expect(await setup.async_setup_component(hass, "cloud", {})).to_be_truthy()

    config_entry = MockConfigEntry(
        domain="test_single", data={"webhook_id": "12345", "cloudhook": False}
    )
    config_entry.add_to_hass(hass)

    flow = config_entries.HANDLERS["test_single"]()
    flow.hass = hass
    flow.context = {
        "source": config_entries.SOURCE_RECONFIGURE,
        "entry_id": config_entry.entry_id,
    }

    result = await flow.async_step_reconfigure()
    expect(result["type"]).to_be(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with (
        patch(
            "hass_nabucasa.cloudhooks.Cloudhooks.async_create",
            return_value={"cloudhook_url": "https://example.com"},
        ) as mock_create,
        patch(
            "hass_nabucasa.Cloud.subscription_expired",
            new_callable=PropertyMock(return_value=False),
        ),
        patch(
            "hass_nabucasa.Cloud.is_logged_in",
            new_callable=PropertyMock(return_value=True),
        ),
        patch(
            "hass_nabucasa.iot_base.BaseIoT.connected",
            new_callable=PropertyMock(return_value=True),
        ),
    ):
        result = await flow.async_step_reconfigure(user_input={})

    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(result["description_placeholders"]).to_equal(
        {"webhook_url": "https://example.com"}
    )
    expect(len(mock_create.mock_calls)).to_equal(1)

    expect(config_entry.data["webhook_id"]).to_equal("12345")
    expect(config_entry.data["cloudhook"]).to_be(True)
