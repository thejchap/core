"""Tests for Home Assistant."""

# Under Tryke there is no conftest auto-load, so fixture modules like
# ``tests.hass_fixtures`` import ``homeassistant.*`` modules which in turn
# bind the un-patched ``partial(...)`` utcnow into dataclass default_factory
# slots (e.g. ``NormalizedNameBaseRegistryEntry.created_at``) before
# ``tests/patch_time.py`` gets a chance to run. We detect Tryke by presence
# of the ``tryke`` module and eagerly import patch_time here — this happens
# when the ``tests`` package is first imported, before any test file's body.
# Under pytest we skip this branch so the existing conftest ordering (which
# expects patch_recorder to run before patch_time) is preserved.
import sys as _sys

if "tryke" in _sys.modules:
    from . import patch_time  # noqa: F401  (side effects only)

del _sys
