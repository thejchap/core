"""Test default blueprints."""

import importlib
import logging
import pathlib

from tryke import expect, test

from homeassistant.components.blueprint import BLUEPRINT_SCHEMA, models
from homeassistant.components.blueprint.const import BLUEPRINT_FOLDER
from homeassistant.util import yaml as yaml_util

LOGGER = logging.getLogger(__name__)


@test.cases(
    test.case("automation", domain="automation"),
)
def default_blueprints(*, domain: str) -> None:
    """Validate a folder of blueprints."""
    integration = importlib.import_module(f"homeassistant.components.{domain}")
    blueprint_folder = pathlib.Path(integration.__file__).parent / BLUEPRINT_FOLDER
    items = list(blueprint_folder.glob("*"))
    expect(len(items) > 0).to_be(True)

    for fil in items:
        LOGGER.info("Processing %s", fil)
        expect(fil.name.endswith(".yaml")).to_be(True)
        data = yaml_util.load_yaml(fil)
        models.Blueprint(data, expected_domain=domain, schema=BLUEPRINT_SCHEMA)
