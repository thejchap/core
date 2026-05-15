"""Tryke fixtures for the dialogflow tests."""

from __future__ import annotations

from tryke import Depends, fixture

from homeassistant import config_entries
from homeassistant.components import dialogflow, intent_script
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client_no_auth as hass_client_no_auth_fixture,
)


@fixture
async def dialogflow_fixture(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
) -> tuple[object, str]:
    """Initialize a Home Assistant server for testing this module."""
    await async_setup_component(hass, dialogflow.DOMAIN, {"dialogflow": {}})
    await async_setup_component(
        hass,
        intent_script.DOMAIN,
        {
            "intent_script": {
                "WhereAreWeIntent": {
                    "speech": {
                        "type": "plain",
                        "text": """
                        {%- if is_state("device_tracker.paulus", "home")
                               and is_state("device_tracker.anne_therese",
                                            "home") -%}
                            You are both home, you silly
                        {%- else -%}
                            Anne Therese is at {{
                                states("device_tracker.anne_therese")
                            }} and Paulus is at {{
                                states("device_tracker.paulus")
                            }}
                        {% endif %}
                    """,
                    }
                },
                "GetZodiacHoroscopeIntent": {
                    "speech": {
                        "type": "plain",
                        "text": "You told us your sign is {{ ZodiacSign }}.",
                    }
                },
                "CallServiceIntent": {
                    "speech": {"type": "plain", "text": "Service called"},
                    "action": {
                        "service": "test.dialogflow",
                        "data_template": {"hello": "{{ ZodiacSign }}"},
                        "entity_id": "switch.test",
                    },
                },
            }
        },
    )

    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:8123"},
    )

    result = await hass.config_entries.flow.async_init(
        "dialogflow", context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM, result

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    webhook_id = result["result"].data["webhook_id"]

    return await hass_client_no_auth(), webhook_id


@fixture
async def calls(
    hass: HomeAssistant = Depends(hass_fixture),
    _fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> list[ServiceCall]:
    """Return a list of Dialogflow calls triggered."""
    captured: list[ServiceCall] = []

    @callback
    def mock_service(call: ServiceCall) -> None:
        """Mock action call."""
        captured.append(call)

    hass.services.async_register("test", "dialogflow", mock_service)

    return captured
