"""Tests for hassfest dependency finder."""

import ast

from tryke import Depends, expect, fixture, test

from script.hassfest.dependencies import ImportCollector


@fixture
def mock_collector() -> ImportCollector:
    """Fixture with import collector that adds all referenced nodes."""
    collector = ImportCollector(None)
    collector.unfiltered_referenced = set()
    collector._add_reference = collector.unfiltered_referenced.add
    return collector


@test
def child_import(mock_collector: ImportCollector = Depends(mock_collector)) -> None:
    """Test detecting a child_import reference."""
    mock_collector.visit(
        ast.parse(
            """

from homeassistant.components import child_import
"""
        )
    )
    expect(mock_collector.unfiltered_referenced).to_equal({"child_import"})


@test
def subimport(mock_collector: ImportCollector = Depends(mock_collector)) -> None:
    """Test detecting a subimport reference."""
    mock_collector.visit(
        ast.parse(
            """

from homeassistant.components.subimport.smart_home import EVENT_ALEXA_SMART_HOME
"""
        )
    )
    expect(mock_collector.unfiltered_referenced).to_equal({"subimport"})


@test
def child_import_field(
    mock_collector: ImportCollector = Depends(mock_collector),
) -> None:
    """Test detecting a child_import_field reference."""
    mock_collector.visit(
        ast.parse(
            """

from homeassistant.components.child_import_field import bla
"""
        )
    )
    expect(mock_collector.unfiltered_referenced).to_equal({"child_import_field"})


@test
def renamed_absolute(mock_collector: ImportCollector = Depends(mock_collector)) -> None:
    """Test detecting a renamed_absolute reference."""
    mock_collector.visit(
        ast.parse(
            """

import homeassistant.components.renamed_absolute as hue
"""
        )
    )
    expect(mock_collector.unfiltered_referenced).to_equal({"renamed_absolute"})


@test
def all_imports(mock_collector: ImportCollector = Depends(mock_collector)) -> None:
    """Test all imports together."""
    mock_collector.visit(
        ast.parse(
            """

from homeassistant.components import child_import

from homeassistant.components.subimport.smart_home import EVENT_ALEXA_SMART_HOME

from homeassistant.components.child_import_field import bla

import homeassistant.components.renamed_absolute as hue
"""
        )
    )
    expect(mock_collector.unfiltered_referenced).to_equal(
        {
            "child_import",
            "subimport",
            "child_import_field",
            "renamed_absolute",
        }
    )
