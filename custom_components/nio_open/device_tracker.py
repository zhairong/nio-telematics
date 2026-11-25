"""Device tracker for the NIO Open Platform."""

from __future__ import annotations

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NioConfigEntry
from .entity import NioEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: NioConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the vehicle tracker."""
    async_add_entities([NioTracker(entry.runtime_data)])


class NioTracker(NioEntity, TrackerEntity):
    """GPS position of the vehicle."""

    _attr_translation_key = "position"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "position_status", "position")

    def _valid(self) -> bool:
        return self._value("posng_valid_type") == "VALID"

    @property
    def latitude(self) -> float | None:
        return self._value("latitude") if self._valid() else None

    @property
    def longitude(self) -> float | None:
        return self._value("longitude") if self._valid() else None
