"""Test the Hunter Douglas Powerview config flow."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.hunterdouglas_powerview.const import DOMAIN
from homeassistant.const import CONF_API_VERSION, CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import hub_patches, mock_setup_entry
from .const import DHCP_DATA, DISCOVERY_DATA, HOMEKIT_DATA, MOCK_SERIAL

from tests.common import MockConfigEntry, async_load_json_object_fixture
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case("v1", api_version=1),
    test.case("v2", api_version=2),
    test.case("v3", api_version=3),
)
async def user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    api_version: int,
) -> None:
    """Test we get the user form."""
    with hub_patches(api_version):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({})

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(f"Powerview Generation {api_version}")
        expect(result2["data"]).to_equal(
            {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
        )
        expect(result2["result"].unique_id).to_equal(MOCK_SERIAL)

        expect(len(setup_entry.mock_calls)).to_equal(1)

        result3 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result3["type"]).to_be(FlowResultType.FORM)
        expect(result3["errors"]).to_equal({})

        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )
        expect(result4["type"]).to_be(FlowResultType.ABORT)
        expect(result4["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "homekit_v2",
        source=DISCOVERY_DATA[0][0],
        discovery_info=DISCOVERY_DATA[0][1],
        api_version=DISCOVERY_DATA[0][2],
    ),
    test.case(
        "homekit_v3",
        source=DISCOVERY_DATA[1][0],
        discovery_info=DISCOVERY_DATA[1][1],
        api_version=DISCOVERY_DATA[1][2],
    ),
    test.case(
        "dhcp_v2",
        source=DISCOVERY_DATA[2][0],
        discovery_info=DISCOVERY_DATA[2][1],
        api_version=DISCOVERY_DATA[2][2],
    ),
    test.case(
        "dhcp_v3",
        source=DISCOVERY_DATA[3][0],
        discovery_info=DISCOVERY_DATA[3][1],
        api_version=DISCOVERY_DATA[3][2],
    ),
    test.case(
        "dhcp_v2_no_name",
        source=DISCOVERY_DATA[4][0],
        discovery_info=DISCOVERY_DATA[4][1],
        api_version=DISCOVERY_DATA[4][2],
    ),
    test.case(
        "zeroconf_v2",
        source=DISCOVERY_DATA[5][0],
        discovery_info=DISCOVERY_DATA[5][1],
        api_version=DISCOVERY_DATA[5][2],
    ),
    test.case(
        "zeroconf_v3",
        source=DISCOVERY_DATA[6][0],
        discovery_info=DISCOVERY_DATA[6][1],
        api_version=DISCOVERY_DATA[6][2],
    ),
)
async def form_homekit_and_dhcp_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    source: str,
    discovery_info: object,
    api_version: int,
) -> None:
    """Test we get the form with homekit and dhcp source."""
    with hub_patches(api_version):
        ignored_config_entry = MockConfigEntry(
            domain=DOMAIN, data={}, source=config_entries.SOURCE_IGNORE
        )
        ignored_config_entry.add_to_hass(hass)

        with patch(
            "homeassistant.components.hunterdouglas_powerview.util.Hub.query_firmware",
            side_effect=TimeoutError,
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": source},
                data=discovery_info,
            )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")

        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=discovery_info,
        )

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {}
        )
        await hass.async_block_till_done()

        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(f"Powerview Generation {api_version}")
        expect(result3["data"]).to_equal(
            {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
        )
        expect(result3["result"].unique_id).to_equal(MOCK_SERIAL)

        expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "homekit_v2",
        source=DISCOVERY_DATA[0][0],
        discovery_info=DISCOVERY_DATA[0][1],
        api_version=DISCOVERY_DATA[0][2],
    ),
    test.case(
        "homekit_v3",
        source=DISCOVERY_DATA[1][0],
        discovery_info=DISCOVERY_DATA[1][1],
        api_version=DISCOVERY_DATA[1][2],
    ),
    test.case(
        "dhcp_v2",
        source=DISCOVERY_DATA[2][0],
        discovery_info=DISCOVERY_DATA[2][1],
        api_version=DISCOVERY_DATA[2][2],
    ),
    test.case(
        "dhcp_v3",
        source=DISCOVERY_DATA[3][0],
        discovery_info=DISCOVERY_DATA[3][1],
        api_version=DISCOVERY_DATA[3][2],
    ),
    test.case(
        "dhcp_v2_no_name",
        source=DISCOVERY_DATA[4][0],
        discovery_info=DISCOVERY_DATA[4][1],
        api_version=DISCOVERY_DATA[4][2],
    ),
    test.case(
        "zeroconf_v2",
        source=DISCOVERY_DATA[5][0],
        discovery_info=DISCOVERY_DATA[5][1],
        api_version=DISCOVERY_DATA[5][2],
    ),
    test.case(
        "zeroconf_v3",
        source=DISCOVERY_DATA[6][0],
        discovery_info=DISCOVERY_DATA[6][1],
        api_version=DISCOVERY_DATA[6][2],
    ),
)
async def form_homekit_and_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    source: str,
    discovery_info: DhcpServiceInfo | ZeroconfServiceInfo,
    api_version: int,
) -> None:
    """Test we get the form with homekit and dhcp source."""
    with hub_patches(api_version):
        ignored_config_entry = MockConfigEntry(
            domain=DOMAIN, data={}, source=config_entries.SOURCE_IGNORE
        )
        ignored_config_entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=discovery_info,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("link")
        expect(result["errors"]).to_be(None)
        expect(result["description_placeholders"]).to_equal(
            {
                CONF_HOST: "1.2.3.4",
                CONF_NAME: f"Powerview Generation {api_version}",
                CONF_API_VERSION: api_version,
            }
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {}
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(f"Powerview Generation {api_version}")
        expect(result2["data"]).to_equal(
            {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
        )
        expect(result2["result"].unique_id).to_equal(MOCK_SERIAL)

        expect(len(setup_entry.mock_calls)).to_equal(1)

        result3 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=discovery_info,
        )
        expect(result3["type"]).to_be(FlowResultType.ABORT)


@test.cases(
    test.case(
        "hk2_dhcp2",
        homekit_source=HOMEKIT_DATA[0][0],
        homekit_discovery=HOMEKIT_DATA[0][1],
        api_version=HOMEKIT_DATA[0][2],
        dhcp_source=DHCP_DATA[0][0],
        dhcp_discovery=DHCP_DATA[0][1],
        dhcp_api_version=DHCP_DATA[0][2],
    ),
    test.case(
        "hk2_dhcp3",
        homekit_source=HOMEKIT_DATA[0][0],
        homekit_discovery=HOMEKIT_DATA[0][1],
        api_version=HOMEKIT_DATA[0][2],
        dhcp_source=DHCP_DATA[1][0],
        dhcp_discovery=DHCP_DATA[1][1],
        dhcp_api_version=DHCP_DATA[1][2],
    ),
    test.case(
        "hk2_dhcp2_no_name",
        homekit_source=HOMEKIT_DATA[0][0],
        homekit_discovery=HOMEKIT_DATA[0][1],
        api_version=HOMEKIT_DATA[0][2],
        dhcp_source=DHCP_DATA[2][0],
        dhcp_discovery=DHCP_DATA[2][1],
        dhcp_api_version=DHCP_DATA[2][2],
    ),
    test.case(
        "hk3_dhcp2",
        homekit_source=HOMEKIT_DATA[1][0],
        homekit_discovery=HOMEKIT_DATA[1][1],
        api_version=HOMEKIT_DATA[1][2],
        dhcp_source=DHCP_DATA[0][0],
        dhcp_discovery=DHCP_DATA[0][1],
        dhcp_api_version=DHCP_DATA[0][2],
    ),
    test.case(
        "hk3_dhcp3",
        homekit_source=HOMEKIT_DATA[1][0],
        homekit_discovery=HOMEKIT_DATA[1][1],
        api_version=HOMEKIT_DATA[1][2],
        dhcp_source=DHCP_DATA[1][0],
        dhcp_discovery=DHCP_DATA[1][1],
        dhcp_api_version=DHCP_DATA[1][2],
    ),
    test.case(
        "hk3_dhcp2_no_name",
        homekit_source=HOMEKIT_DATA[1][0],
        homekit_discovery=HOMEKIT_DATA[1][1],
        api_version=HOMEKIT_DATA[1][2],
        dhcp_source=DHCP_DATA[2][0],
        dhcp_discovery=DHCP_DATA[2][1],
        dhcp_api_version=DHCP_DATA[2][2],
    ),
)
async def discovered_by_homekit_and_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    homekit_source: str,
    homekit_discovery: ZeroconfServiceInfo,
    api_version: int,
    dhcp_source: str,
    dhcp_discovery: DhcpServiceInfo,
    dhcp_api_version: int,
) -> None:
    """Test we get the form with homekit and abort for dhcp source when we get both."""
    with hub_patches(api_version):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_HOMEKIT},
            data=homekit_discovery,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("link")

        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=dhcp_discovery,
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("already_in_progress")


@test.cases(
    test.case("v1", api_version=1),
    test.case("v2", api_version=2),
    test.case("v3", api_version=3),
)
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    api_version: int,
) -> None:
    """Test we handle cannot connect error."""
    with hub_patches(api_version):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "homeassistant.components.hunterdouglas_powerview.util.Hub.query_firmware",
            side_effect=TimeoutError,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "1.2.3.4"},
            )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(f"Powerview Generation {api_version}")
        expect(result3["data"]).to_equal(
            {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
        )
        expect(result3["result"].unique_id).to_equal(MOCK_SERIAL)

        expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("v1", api_version=1),
    test.case("v2", api_version=2),
    test.case("v3", api_version=3),
)
async def form_no_data(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    api_version: int,
) -> None:
    """Test we handle no data being returned from the hub."""
    with hub_patches(api_version):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with (
            patch(
                "homeassistant.components.hunterdouglas_powerview.util.Hub.request_raw_data",
                return_value={},
            ),
            patch(
                "homeassistant.components.hunterdouglas_powerview.util.Hub.request_home_data",
                return_value={},
            ),
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "1.2.3.4"},
            )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(f"Powerview Generation {api_version}")
        expect(result3["data"]).to_equal(
            {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
        )
        expect(result3["result"].unique_id).to_equal(MOCK_SERIAL)

        expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("v1", api_version=1),
    test.case("v2", api_version=2),
    test.case("v3", api_version=3),
)
async def form_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    api_version: int,
) -> None:
    """Test we handle unknown exception."""
    with hub_patches(api_version):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "homeassistant.components.hunterdouglas_powerview.util.Hub.query_firmware",
            side_effect=SyntaxError,
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "1.2.3.4"},
            )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "unknown"})

        result2 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(f"Powerview Generation {api_version}")
        expect(result2["data"]).to_equal(
            {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
        )
        expect(result2["result"].unique_id).to_equal(MOCK_SERIAL)

        expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(test.case("v3", api_version=3))
async def form_unsupported_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    *,
    api_version: int,
) -> None:
    """Test unsupported device failure."""
    with hub_patches(api_version):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "homeassistant.components.hunterdouglas_powerview.util.Hub.request_raw_data",
            return_value=await async_load_json_object_fixture(
                hass, "gen3/gateway/secondary.json", DOMAIN
            ),
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_HOST: "1.2.3.4"},
            )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "unsupported_device"})

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_HOST: "1.2.3.4"},
        )

        expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result3["title"]).to_equal(f"Powerview Generation {api_version}")
        expect(result3["data"]).to_equal(
            {CONF_HOST: "1.2.3.4", CONF_API_VERSION: api_version}
        )
        expect(result3["result"].unique_id).to_equal(MOCK_SERIAL)

        expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("v1", api_version=1),
    test.case("v2", api_version=2),
    test.case("v3", api_version=3),
)
async def migrate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    *,
    api_version: int,
) -> None:
    """Test migrate to newest version."""
    with hub_patches(api_version):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"host": "1.2.3.4"},
            unique_id=MOCK_SERIAL,
            version=1,
            minor_version=1,
        )
        entry.add_to_hass(hass)

        entity_registry.async_get_or_create(
            domain="cover",
            platform="hunterdouglas_powerview",
            unique_id=123,
            config_entry=entry,
        )
        entity_registry.async_get_or_create(
            domain="cover",
            platform="hunterdouglas_powerview",
            unique_id="old_unique_id",
            config_entry=entry,
        )

        expect(entry.version).to_equal(1)
        expect(entry.minor_version).to_equal(1)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(entry.version).to_equal(1)
        expect(entry.minor_version).to_equal(2)

        registry_entries = er.async_entries_for_config_entry(
            entity_registry, entry.entry_id
        )

        for reg_entry in registry_entries:
            expect(reg_entry.unique_id.startswith(f"{entry.unique_id}_")).to_be(True)
