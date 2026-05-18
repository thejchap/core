"""Test repairs for workday (tryke port)."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.workday.const import CONF_REMOVE_HOLIDAYS, DOMAIN
from homeassistant.const import CONF_COUNTRY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from tests.common import ANY
from tests.components.repairs import process_repair_fix_flow, start_repair_fix_flow
from tests.components.workday import (
    TEST_CONFIG_INCORRECT_COUNTRY,
    TEST_CONFIG_INCORRECT_PROVINCE,
    TEST_CONFIG_REMOVE_DATE,
    TEST_CONFIG_REMOVE_NAMED,
    init_integration,
)
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    hass_ws_client as hass_ws_client_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test
async def bad_country(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test fixing bad country."""
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    entry = await init_integration(hass, TEST_CONFIG_INCORRECT_COUNTRY)

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_falsy()

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"]) > 0).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_country":
            issue = i
    expect(issue).to_be_truthy()

    data = await start_repair_fix_flow(client, DOMAIN, "bad_country")

    flow_id = data["flow_id"]
    expect(data["description_placeholders"]).to_equal({"title": entry.title})
    expect(data["step_id"]).to_equal("country")

    data = await process_repair_fix_flow(client, flow_id, json={"country": "DE"})

    data = await process_repair_fix_flow(client, flow_id, json={"province": "HB"})

    expect(data["type"]).to_equal("create_entry")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_truthy()

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_country":
            issue = i
    expect(issue).to_be_falsy()


@test
async def bad_country_none(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test fixing bad country with no province."""
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    entry = await init_integration(hass, TEST_CONFIG_INCORRECT_COUNTRY)

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_falsy()

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"]) > 0).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_country":
            issue = i
    expect(issue).to_be_truthy()

    data = await start_repair_fix_flow(client, DOMAIN, "bad_country")

    flow_id = data["flow_id"]
    expect(data["description_placeholders"]).to_equal({"title": entry.title})
    expect(data["step_id"]).to_equal("country")

    data = await process_repair_fix_flow(client, flow_id, json={"country": "DE"})

    data = await process_repair_fix_flow(client, flow_id, json={})

    expect(data["type"]).to_equal("create_entry")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_truthy()

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_country":
            issue = i
    expect(issue).to_be_falsy()


@test
async def bad_country_no_province(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test fixing bad country."""
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    entry = await init_integration(hass, TEST_CONFIG_INCORRECT_COUNTRY)

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_falsy()

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"]) > 0).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_country":
            issue = i
    expect(issue).to_be_truthy()

    data = await start_repair_fix_flow(client, DOMAIN, "bad_country")

    flow_id = data["flow_id"]
    expect(data["description_placeholders"]).to_equal({"title": entry.title})
    expect(data["step_id"]).to_equal("country")

    data = await process_repair_fix_flow(client, flow_id, json={"country": "SE"})

    expect(data["type"]).to_equal("create_entry")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_truthy()

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_country":
            issue = i
    expect(issue).to_be_falsy()


@test
async def bad_province(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test fixing bad province."""
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    entry = await init_integration(hass, TEST_CONFIG_INCORRECT_PROVINCE)

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_falsy()

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"]) > 0).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_province":
            issue = i
    expect(issue).to_be_truthy()

    data = await start_repair_fix_flow(client, DOMAIN, "bad_province")

    flow_id = data["flow_id"]
    expect(data["description_placeholders"]).to_equal(
        {CONF_COUNTRY: "DE", "title": entry.title}
    )
    expect(data["step_id"]).to_equal("province")

    data = await process_repair_fix_flow(client, flow_id, json={"province": "BW"})

    expect(data["type"]).to_equal("create_entry")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_truthy()

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_province":
            issue = i
    expect(issue).to_be_falsy()


@test
async def bad_province_none(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test fixing bad province selecting none."""
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    entry = await init_integration(hass, TEST_CONFIG_INCORRECT_PROVINCE)

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_falsy()

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"]) > 0).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_province":
            issue = i
    expect(issue).to_be_truthy()

    data = await start_repair_fix_flow(client, DOMAIN, "bad_province")

    flow_id = data["flow_id"]
    expect(data["description_placeholders"]).to_equal(
        {CONF_COUNTRY: "DE", "title": entry.title}
    )
    expect(data["step_id"]).to_equal("province")

    data = await process_repair_fix_flow(client, flow_id, json={})

    expect(data["type"]).to_equal("create_entry")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_truthy()

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_province":
            issue = i
    expect(issue).to_be_falsy()


@test
async def bad_named_holiday(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test fixing bad named holiday."""
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    entry = await init_integration(hass, TEST_CONFIG_REMOVE_NAMED)

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_truthy()

    issues = issue_registry.issues.keys()
    for issue_key in issues:
        if issue_key[0] == DOMAIN:
            expect(issue_key[1].startswith("bad_named")).to_be_truthy()

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"]) > 0).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_named_holiday-1-not_a_holiday":
            issue = i
    expect(issue).to_be_truthy()

    data = await start_repair_fix_flow(
        client, DOMAIN, "bad_named_holiday-1-not_a_holiday"
    )

    flow_id = data["flow_id"]
    expect(data["description_placeholders"]).to_equal(
        {
            CONF_COUNTRY: "US",
            CONF_REMOVE_HOLIDAYS: "Not a Holiday",
            "title": entry.title,
        }
    )
    expect(data["step_id"]).to_equal("fix_remove_holiday")

    data = await process_repair_fix_flow(
        client, flow_id, json={"remove_holidays": ["Christmas", "Not exist 2"]}
    )

    expect(data["errors"]).to_equal({CONF_REMOVE_HOLIDAYS: "remove_holiday_error"})

    data = await process_repair_fix_flow(
        client, flow_id, json={"remove_holidays": ["Christmas", "Thanksgiving"]}
    )

    expect(data["type"]).to_equal("create_entry")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_truthy()

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_named_holiday-1-not_a_holiday":
            issue = i
    expect(issue).to_be_falsy()


@test
async def bad_date_holiday(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test fixing bad date holiday."""
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    entry = await init_integration(hass, TEST_CONFIG_REMOVE_DATE)

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_truthy()

    issues = issue_registry.issues.keys()
    for issue_key in issues:
        if issue_key[0] == DOMAIN:
            expect(issue_key[1].startswith("bad_date")).to_be_truthy()

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"]) > 0).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_date_holiday-1-2024_02_05":
            issue = i
    expect(issue).to_be_truthy()

    data = await start_repair_fix_flow(client, DOMAIN, "bad_date_holiday-1-2024_02_05")

    flow_id = data["flow_id"]
    expect(data["description_placeholders"]).to_equal(
        {
            CONF_COUNTRY: "US",
            CONF_REMOVE_HOLIDAYS: "2024-02-05",
            "title": entry.title,
        }
    )
    expect(data["step_id"]).to_equal("fix_remove_holiday")

    data = await process_repair_fix_flow(
        client, flow_id, json={"remove_holidays": ["2024-02-06"]}
    )

    expect(data["type"]).to_equal("create_entry")
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.workday_sensor")
    expect(state).to_be_truthy()

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_date_holiday-1-2024_02_05":
            issue = i
    expect(issue).to_be_falsy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "bad_date_holiday-1-2024_02_06":
            issue = i
    expect(issue).to_be_truthy()


@test
async def other_fixable_issues(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test fixing other fixable issues."""
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    await init_integration(hass, TEST_CONFIG_INCORRECT_PROVINCE)

    ws_client = await hass_ws_client(hass)
    client = await hass_client()

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()

    issue = {
        "breaks_in_ha_version": "2022.9.0dev0",
        "domain": DOMAIN,
        "issue_id": "issue_1",
        "is_fixable": True,
        "learn_more_url": "",
        "severity": "error",
        "translation_key": "issue_1",
    }
    ir.async_create_issue(
        hass,
        issue["domain"],
        issue["issue_id"],
        breaks_in_ha_version=issue["breaks_in_ha_version"],
        is_fixable=issue["is_fixable"],
        is_persistent=False,
        learn_more_url=None,
        severity=issue["severity"],
        translation_key=issue["translation_key"],
    )

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    results = msg["result"]["issues"]
    expect(
        {
            "breaks_in_ha_version": "2022.9.0dev0",
            "created": ANY,
            "dismissed_version": None,
            "domain": "workday",
            "is_fixable": True,
            "issue_domain": None,
            "issue_id": "issue_1",
            "learn_more_url": None,
            "severity": "error",
            "translation_key": "issue_1",
            "translation_placeholders": None,
            "ignored": False,
        }
        in results
    ).to_be_truthy()

    data = await start_repair_fix_flow(client, DOMAIN, "issue_1")

    flow_id = data["flow_id"]
    expect(data["step_id"]).to_equal("confirm")

    data = await process_repair_fix_flow(client, flow_id)

    expect(data["type"]).to_equal("create_entry")
    await hass.async_block_till_done()
