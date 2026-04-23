"""Tryke fixtures for Picnic tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture


@fixture
def picnic_api() -> Generator[MagicMock]:
    """Create PicnicAPI mock with set response data."""
    auth_token = "af3wh738j3fa28l9fa23lhiufahu7l"
    auth_data = {
        "user_id": "f29-2a6-o32n",
        "address": {
            "street": "Teststreet",
            "house_number": 123,
            "house_number_ext": "b",
        },
    }
    with patch(
        "homeassistant.components.picnic.config_flow.PicnicAPI",
    ) as picnic_mock:
        instance = picnic_mock.return_value
        instance.session.auth_token = auth_token
        instance.get_user.return_value = auth_data
        instance.login.return_value = None
        instance.generate_2fa_code.return_value = None
        instance.verify_2fa_code.return_value = None

        yield picnic_mock
