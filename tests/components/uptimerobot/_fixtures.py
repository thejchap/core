"""Tryke fixtures for the UptimeRobot tests."""

from __future__ import annotations

# UptimeRobot tests have no @pytest.fixture-style fixtures of their own —
# they rely on shared ``tests/components/uptimerobot/common.py`` constants /
# helpers and the global ``hass`` fixture. This file exists for parity with
# other re-ported integrations; if a future port needs a fixture, add it
# here.
