"""Tests for entity translation wiring (translation_key <-> translations/*.json)."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.nio_open.binary_sensor import BINARY_SENSORS
from custom_components.nio_open.sensor import SENSORS

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "nio_open"
LANGUAGES = ("en", "zh-Hans", "de")

# Entities whose translation_key is set directly via `_attr_translation_key`
# rather than through an EntityDescription.
EXTRA_KEYS = {
    "binary_sensor": {"door_status_charge_port"},
    "device_tracker": {"position"},
}


def test_entity_descriptions_use_translation_key() -> None:
    """Every generated description's translation_key must match its unique key."""
    for description in (*SENSORS, *BINARY_SENSORS):
        assert description.translation_key == description.key


def test_translation_files_cover_all_entity_keys() -> None:
    """strings.json and every language file must define a name for each entity key."""
    expected = {
        "sensor": {d.key for d in SENSORS},
        "binary_sensor": {d.key for d in BINARY_SENSORS} | EXTRA_KEYS["binary_sensor"],
        "device_tracker": EXTRA_KEYS["device_tracker"],
    }

    files = [COMPONENT_DIR / "strings.json"] + [
        COMPONENT_DIR / "translations" / f"{lang}.json" for lang in LANGUAGES
    ]
    for path in files:
        data = json.loads(path.read_text())
        entity = data.get("entity", {})
        for domain, keys in expected.items():
            defined = set(entity.get(domain, {}))
            missing = keys - defined
            assert not missing, f"{path.name} is missing {domain} keys: {missing}"
            for key in keys:
                assert entity[domain][key].get("name"), f"{path.name} has an empty name for {domain}.{key}"
