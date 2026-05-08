"""Test HomematicIP Cloud helper functions."""

import json

from tryke import expect, test

from homeassistant.components.homematicip_cloud.helpers import is_error_response


@test
async def is_error_response_test() -> None:
    """Test, if an response is a normal result or an error."""
    expect(bool(is_error_response("True"))).to_be(False)
    expect(bool(is_error_response(True))).to_be(False)
    expect(bool(is_error_response(""))).to_be(False)
    expect(
        bool(
            is_error_response(
                json.loads(
                    '{"errorCode": "INVALID_NUMBER_PARAMETER_VALUE", "minValue": 0.0, "maxValue": 1.01}'
                )
            )
        )
    ).to_be(True)
    expect(bool(is_error_response(json.loads('{"errorCode": ""}')))).to_be(False)
