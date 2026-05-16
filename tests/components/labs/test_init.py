"""Tests for the Home Assistant Labs integration setup."""

from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.labs import (
    EVENT_LABS_UPDATED,
    EventLabsUpdatedData,
    async_is_preview_feature_enabled,
    async_listen,
    async_subscribe_preview_feature,
    async_update_preview_feature,
)
from homeassistant.components.labs.const import DOMAIN, LABS_DATA
from homeassistant.components.labs.models import LabPreviewFeature
from homeassistant.core import HomeAssistant
from homeassistant.loader import Integration
from homeassistant.setup import async_setup_component

from . import assert_stored_labs_data

from tests.common import async_capture_events
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Module-level anchor fixture."""
    return 0


@test
async def async_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the Labs integration setup."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    expect("labs/list" in hass.data["websocket_api"]).to_be(True)
    expect("labs/update" in hass.data["websocket_api"]).to_be(True)


@test
async def async_is_preview_feature_enabled_not_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test checking if preview feature is enabled before setup returns False."""
    result = async_is_preview_feature_enabled(hass, "kitchen_sink", "special_repair")
    expect(result).to_be(False)


@test
async def async_is_preview_feature_enabled_nonexistent(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test checking if non-existent preview feature is enabled."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    result = async_is_preview_feature_enabled(
        hass, "kitchen_sink", "nonexistent_feature"
    )
    expect(result).to_be(False)


@test
async def async_is_preview_feature_enabled_when_enabled(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test checking if preview feature is enabled."""
    hass.config.components.add("kitchen_sink")

    hass_storage["core.labs"] = {
        "version": 1,
        "minor_version": 1,
        "key": "core.labs",
        "data": {
            "preview_feature_status": [
                {"domain": "kitchen_sink", "preview_feature": "special_repair"}
            ]
        },
    }

    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    result = async_is_preview_feature_enabled(hass, "kitchen_sink", "special_repair")
    expect(result).to_be(True)


@test
async def async_is_preview_feature_enabled_when_disabled(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test checking if preview feature is disabled (not in storage)."""
    hass.config.components.add("kitchen_sink")

    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    result = async_is_preview_feature_enabled(hass, "kitchen_sink", "special_repair")
    expect(result).to_be(False)


@test.cases(
    test.case(
        "single_stale",
        features_to_store=[
            {"domain": "kitchen_sink", "preview_feature": "special_repair"},
            {"domain": "nonexistent_domain", "preview_feature": "fake_feature"},
        ],
        expected_enabled=[("kitchen_sink", "special_repair")],
        expected_cleaned=[("nonexistent_domain", "fake_feature")],
        expected_cleaned_store=[
            {"domain": "kitchen_sink", "preview_feature": "special_repair"}
        ],
    ),
    test.case(
        "multiple_stale",
        features_to_store=[
            {"domain": "kitchen_sink", "preview_feature": "special_repair"},
            {"domain": "stale_domain_1", "preview_feature": "old_feature"},
            {"domain": "stale_domain_2", "preview_feature": "another_old"},
            {"domain": "stale_domain_3", "preview_feature": "yet_another"},
        ],
        expected_enabled=[("kitchen_sink", "special_repair")],
        expected_cleaned=[
            ("stale_domain_1", "old_feature"),
            ("stale_domain_2", "another_old"),
            ("stale_domain_3", "yet_another"),
        ],
        expected_cleaned_store=[
            {"domain": "kitchen_sink", "preview_feature": "special_repair"}
        ],
    ),
    test.case(
        "all_cleaned",
        features_to_store=[{"domain": "nonexistent", "preview_feature": "fake"}],
        expected_enabled=[],
        expected_cleaned=[("nonexistent", "fake")],
        expected_cleaned_store=[],
    ),
)
async def storage_cleanup_stale_features(
    features_to_store: list[dict[str, str]],
    expected_enabled: list[tuple[str, str]],
    expected_cleaned: list[tuple[str, str]],
    expected_cleaned_store: list[dict[str, str]],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test that stale preview features are removed from storage on setup."""
    if expected_enabled:
        hass.config.components.add("kitchen_sink")

    hass_storage["core.labs"] = {
        "version": 1,
        "minor_version": 1,
        "key": "core.labs",
        "data": {"preview_feature_status": features_to_store},
    }

    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    for domain, feature in expected_enabled:
        expect(async_is_preview_feature_enabled(hass, domain, feature)).to_be(True)

    for domain, feature in expected_cleaned:
        expect(async_is_preview_feature_enabled(hass, domain, feature)).to_be(False)

    assert_stored_labs_data(hass_storage, expected_cleaned_store)


@test.cases(
    test.case(
        "enabled_match",
        domain="kitchen_sink",
        preview_feature="special_repair",
        expected=True,
    ),
    test.case(
        "other_domain",
        domain="other",
        preview_feature="nonexistent",
        expected=False,
    ),
    test.case(
        "kitchen_sink_missing_feature",
        domain="kitchen_sink",
        preview_feature="nonexistent",
        expected=False,
    ),
)
async def async_is_preview_feature_enabled_param(
    domain: str,
    preview_feature: str,
    expected: bool,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test async_is_preview_feature_enabled."""
    hass_storage["core.labs"] = {
        "version": 1,
        "minor_version": 1,
        "key": "core.labs",
        "data": {
            "preview_feature_status": [
                {"domain": "kitchen_sink", "preview_feature": "special_repair"}
            ]
        },
    }

    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    result = async_is_preview_feature_enabled(hass, domain, preview_feature)
    expect(result is expected).to_be(True)


@test
async def preview_feature_full_key(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that preview feature full_key property returns correct format."""
    feature = LabPreviewFeature(
        domain="test_domain",
        preview_feature="test_feature",
        feedback_url="https://feedback.example.com",
    )

    expect(feature.full_key).to_equal("test_domain.test_feature")


@test
async def preview_feature_to_dict_with_all_urls(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test LabPreviewFeature.to_dict with all URLs populated."""
    feature = LabPreviewFeature(
        domain="test_domain",
        preview_feature="test_feature",
        feedback_url="https://feedback.example.com",
        learn_more_url="https://learn.example.com",
        report_issue_url="https://issue.example.com",
    )

    result = feature.to_dict(enabled=True)

    expect(result).to_equal(
        {
            "preview_feature": "test_feature",
            "domain": "test_domain",
            "enabled": True,
            "is_built_in": True,
            "feedback_url": "https://feedback.example.com",
            "learn_more_url": "https://learn.example.com",
            "report_issue_url": "https://issue.example.com",
        }
    )


@test
async def preview_feature_to_dict_with_no_urls(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test LabPreviewFeature.to_dict with no URLs (all None)."""
    feature = LabPreviewFeature(
        domain="test_domain",
        preview_feature="test_feature",
    )

    result = feature.to_dict(enabled=False)

    expect(result).to_equal(
        {
            "preview_feature": "test_feature",
            "domain": "test_domain",
            "enabled": False,
            "is_built_in": True,
            "feedback_url": None,
            "learn_more_url": None,
            "report_issue_url": None,
        }
    )


@test
async def custom_integration_with_preview_features(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that custom integrations with preview features are loaded."""
    mock_integration = Mock(spec=Integration)
    mock_integration.domain = "custom_test"
    mock_integration.preview_features = {
        "test_feature": {
            "feedback_url": "https://feedback.test",
            "learn_more_url": "https://learn.test",
        }
    }

    with patch(
        "homeassistant.components.labs.async_get_custom_components",
        return_value={"custom_test": mock_integration},
    ):
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()

    expect(
        async_is_preview_feature_enabled(hass, "custom_test", "test_feature")
    ).to_be(False)


@test.cases(
    test.case("built_in", is_custom=False, expected_is_built_in=True),
    test.case("custom", is_custom=True, expected_is_built_in=False),
)
async def preview_feature_is_built_in_flag(
    is_custom: bool,
    expected_is_built_in: bool,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that preview features have correct is_built_in flag."""
    if is_custom:
        mock_integration = Mock(spec=Integration)
        mock_integration.domain = "custom_test"
        mock_integration.preview_features = {
            "custom_feature": {"feedback_url": "https://feedback.test"}
        }
        with patch(
            "homeassistant.components.labs.async_get_custom_components",
            return_value={"custom_test": mock_integration},
        ):
            expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
            await hass.async_block_till_done()
        feature_key = "custom_test.custom_feature"
    else:
        hass.config.components.add("kitchen_sink")
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()
        feature_key = "kitchen_sink.special_repair"

    labs_data = hass.data[LABS_DATA]
    expect(feature_key in labs_data.preview_features).to_be(True)
    feature = labs_data.preview_features[feature_key]
    expect(feature.is_built_in is expected_is_built_in).to_be(True)


@test.cases(
    test.case("true", is_built_in=True, expected_default=True),
    test.case("false", is_built_in=False, expected_default=False),
    test.case("none_default", is_built_in=None, expected_default=True),
)
async def preview_feature_to_dict_is_built_in(
    is_built_in: bool | None,
    expected_default: bool,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that to_dict correctly handles is_built_in field."""
    if is_built_in is None:
        feature = LabPreviewFeature(
            domain="test_domain",
            preview_feature="test_feature",
        )
    else:
        feature = LabPreviewFeature(
            domain="test_domain",
            preview_feature="test_feature",
            is_built_in=is_built_in,
        )

    expect(feature.is_built_in is expected_default).to_be(True)
    result = feature.to_dict(enabled=True)
    expect(result["is_built_in"] is expected_default).to_be(True)


@test
async def async_listen_helper(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the async_listen helper function for preview feature events."""
    hass.config.components.add("kitchen_sink")

    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    listener_calls: list[str] = []

    def test_listener() -> None:
        """Test listener callback."""
        listener_calls.append("called")

    unsub = async_listen(
        hass,
        domain="kitchen_sink",
        preview_feature="special_repair",
        listener=test_listener,
    )

    expect("calls `async_listen` which is deprecated" in caplog.text).to_be(True)

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    expect(len(listener_calls)).to_equal(1)

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "other_feature",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    expect(len(listener_calls)).to_equal(1)

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "other_domain",
            "preview_feature": "special_repair",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    expect(len(listener_calls)).to_equal(1)

    unsub()

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    expect(len(listener_calls)).to_equal(1)


@test
async def async_subscribe_preview_feature_helper(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_subscribe_preview_feature helper."""
    hass.config.components.add("kitchen_sink")

    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    calls: list[EventLabsUpdatedData] = []

    async def listener(event_data: EventLabsUpdatedData) -> None:
        """Test listener callback."""
        calls.append(event_data)

    unsub = async_subscribe_preview_feature(
        hass,
        domain="kitchen_sink",
        preview_feature="special_repair",
        listener=listener,
    )

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0]["enabled"]).to_be(True)

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "other_feature",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "other_domain",
            "preview_feature": "special_repair",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": False,
        },
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(2)
    expect(calls[1]["enabled"]).to_be(False)

    unsub()

    hass.bus.async_fire(
        EVENT_LABS_UPDATED,
        {
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        },
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(2)


@test
async def async_update_preview_feature_test(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test enabling and disabling a preview feature using the helper function."""
    hass.config.components.add("kitchen_sink")

    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    events = async_capture_events(hass, EVENT_LABS_UPDATED)

    await async_update_preview_feature(
        hass, "kitchen_sink", "special_repair", enabled=True
    )
    await hass.async_block_till_done()

    expect(
        async_is_preview_feature_enabled(hass, "kitchen_sink", "special_repair")
    ).to_be(True)

    expect(len(events)).to_equal(1)
    expect(events[0].data["domain"]).to_equal("kitchen_sink")
    expect(events[0].data["preview_feature"]).to_equal("special_repair")
    expect(events[0].data["enabled"]).to_be(True)

    assert_stored_labs_data(
        hass_storage,
        [{"domain": "kitchen_sink", "preview_feature": "special_repair"}],
    )

    await async_update_preview_feature(
        hass, "kitchen_sink", "special_repair", enabled=False
    )
    await hass.async_block_till_done()

    expect(
        async_is_preview_feature_enabled(hass, "kitchen_sink", "special_repair")
    ).to_be(False)

    expect(len(events)).to_equal(2)
    expect(events[1].data["domain"]).to_equal("kitchen_sink")
    expect(events[1].data["preview_feature"]).to_equal("special_repair")
    expect(events[1].data["enabled"]).to_be(False)

    assert_stored_labs_data(hass_storage, [])


@test
async def async_update_preview_feature_not_found(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating a preview feature that doesn't exist raises."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    async with expect_raises_async(
        ValueError, match="Preview feature nonexistent.feature not found"
    ):
        await async_update_preview_feature(hass, "nonexistent", "feature", enabled=True)
