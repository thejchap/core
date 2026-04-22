"""Tests for hassfest integration_type."""

from pathlib import Path
from unittest.mock import patch

from tryke import expect, test

from script.hassfest import integration_type
from script.hassfest.model import Config, Integration

from . import get_integration


def _make_config() -> Config:
    """Build a fresh Config for each test."""
    return Config(
        root=Path(".").absolute(),
        specific_integrations=None,
        action="validate",
        requirements=True,
    )


def _get_integration(domain: str, config: Config, manifest_extra: dict) -> Integration:
    """Helper to create an integration with extra manifest keys."""
    integration = get_integration(domain, config)
    integration.manifest.update(manifest_extra)
    return integration


@test
def integration_with_config_flow_and_integration_type() -> None:
    """Integration with config_flow and integration_type should pass without errors."""
    config = _make_config()
    with patch.object(Integration, "core", return_value=True):
        integrations = {
            "test": _get_integration(
                "test",
                config,
                {"config_flow": True, "integration_type": "device"},
            )
        }
        integration_type.validate(integrations, config)
        expect(integrations["test"].errors).to_equal([])


@test
def integration_with_config_flow_missing_integration_type() -> None:
    """Integration with config_flow but no integration_type and not in allowlist should error."""
    config = _make_config()
    with patch.object(Integration, "core", return_value=True):
        integrations = {
            "test": _get_integration(
                "test",
                config,
                {"config_flow": True},
            )
        }
        integration_type.validate(integrations, config)
        expect(len(integrations["test"].errors)).to_equal(1)
        expect(
            "missing an `integration_type`" in integrations["test"].errors[0].error
        ).to_be(True)


@test
def integration_with_config_flow_in_allowlist() -> None:
    """Integration with config_flow but no integration_type and in allowlist should pass."""
    config = _make_config()
    with patch.object(Integration, "core", return_value=True):
        domain = next(iter(integration_type.MISSING_INTEGRATION_TYPE))
        integrations = {
            domain: _get_integration(
                domain,
                config,
                {"config_flow": True},
            )
        }
        integration_type.validate(integrations, config)
        expect(integrations[domain].errors).to_equal([])


@test
def integration_with_integration_type_still_in_allowlist() -> None:
    """Integration with integration_type but still in allowlist should error."""
    config = _make_config()
    with patch.object(Integration, "core", return_value=True):
        domain = next(iter(integration_type.MISSING_INTEGRATION_TYPE))
        integrations = {
            domain: _get_integration(
                domain,
                config,
                {"config_flow": True, "integration_type": "device"},
            )
        }
        integration_type.validate(integrations, config)
        expect(len(integrations[domain].errors)).to_equal(1)
        expect(
            "still listed in MISSING_INTEGRATION_TYPE"
            in integrations[domain].errors[0].error
        ).to_be(True)


@test
def integration_without_config_flow_skipped() -> None:
    """Integration without config_flow should be skipped regardless of integration_type."""
    config = _make_config()
    with patch.object(Integration, "core", return_value=True):
        integrations = {
            "test": _get_integration(
                "test",
                config,
                {},
            )
        }
        integration_type.validate(integrations, config)
        expect(integrations["test"].errors).to_equal([])
