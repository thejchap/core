"""Test repair flows."""

from tryke import expect, test

from homeassistant.components.assist_pipeline.repair_flows import (
    AssistInProgressDeprecatedRepairFlow,
)


@test.cases(
    test.case("none", data=None),
    test.case("empty_dict", data={}),
    test.case(
        "missing_keys", data={"entity_id": "blah", "entity_uuid": "12345"}
    ),
)
def assist_in_progress_deprecated_flow_requires_data(data: dict | None) -> None:
    """Test AssistInProgressDeprecatedRepairFlow requires data."""
    expect(lambda: AssistInProgressDeprecatedRepairFlow(data)).to_raise(ValueError)
