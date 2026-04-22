"""Tests for hassfest version."""

from pathlib import Path

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from script.hassfest.manifest import (
    CUSTOM_INTEGRATION_MANIFEST_SCHEMA,
    validate_version,
)
from script.hassfest.model import Config, Integration


@fixture
def integration() -> Integration:
    """Fixture for hassfest integration model."""
    integration = Integration(
        Path(),
        _config=Config(
            root=Path(".").absolute(),
            specific_integrations=None,
            action="validate",
            requirements=True,
        ),
    )
    integration._manifest = {
        "domain": "test",
        "documentation": "https://example.com",
        "name": "test",
        "codeowners": ["@awesome"],
    }
    return integration


@test
def validate_version_no_key(integration: Integration = Depends(integration)) -> None:
    """Test validate version with no key."""
    validate_version(integration)
    expect(
        "No 'version' key in the manifest file."
        in [x.error for x in integration.errors]
    ).to_be(True)


@test
def validate_custom_integration_manifest(
    integration: Integration = Depends(integration),
) -> None:
    """Test validate custom integration manifest."""

    integration.manifest["version"] = "lorem_ipsum"
    expect(lambda: CUSTOM_INTEGRATION_MANIFEST_SCHEMA(integration.manifest)).to_raise(
        vol.Invalid
    )

    integration.manifest["version"] = None
    expect(lambda: CUSTOM_INTEGRATION_MANIFEST_SCHEMA(integration.manifest)).to_raise(
        vol.Invalid
    )

    integration.manifest["version"] = "1"
    schema = CUSTOM_INTEGRATION_MANIFEST_SCHEMA(integration.manifest)
    expect(schema["version"]).to_equal("1")
