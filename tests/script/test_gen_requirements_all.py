"""Tests for the gen_requirements_all script."""

from unittest.mock import patch

from tryke import expect, test

from script import gen_requirements_all


@test
def overrides_normalized() -> None:
    """Test override lists are using normalized package names."""
    for req in gen_requirements_all.EXCLUDED_REQUIREMENTS_ALL:
        expect(req).to_equal(gen_requirements_all._normalize_package_name(req))
    for req in gen_requirements_all.INCLUDED_REQUIREMENTS_WHEELS:
        expect(req).to_equal(gen_requirements_all._normalize_package_name(req))
    for overrides in gen_requirements_all.OVERRIDDEN_REQUIREMENTS_ACTIONS.values():
        for req in overrides["exclude"]:
            expect(req).to_equal(gen_requirements_all._normalize_package_name(req))
        for req in overrides["include"]:
            expect(req).to_equal(gen_requirements_all._normalize_package_name(req))


@test
def include_overrides_subsets() -> None:
    """Test packages in include override lists are present in the exclude list."""
    for req in gen_requirements_all.INCLUDED_REQUIREMENTS_WHEELS:
        expect(req in gen_requirements_all.EXCLUDED_REQUIREMENTS_ALL).to_be(True)
    for overrides in gen_requirements_all.OVERRIDDEN_REQUIREMENTS_ACTIONS.values():
        for req in overrides["include"]:
            expect(req in gen_requirements_all.EXCLUDED_REQUIREMENTS_ALL).to_be(True)


@test
def requirement_override_markers() -> None:
    """Test override markers are applied to the correct requirements."""
    data = {
        "pytest": {
            "exclude": set(),
            "include": set(),
            "markers": {"env-canada": "python_version<'3.13'"},
        }
    }
    with patch.dict(
        gen_requirements_all.OVERRIDDEN_REQUIREMENTS_ACTIONS, data, clear=True
    ):
        expect(
            gen_requirements_all.process_action_requirement(
                "env-canada==0.8.0", "pytest"
            )
        ).to_equal("env-canada==0.8.0;python_version<'3.13'")
        expect(
            gen_requirements_all.process_action_requirement("other==1.0", "pytest")
        ).to_equal("other==1.0")
