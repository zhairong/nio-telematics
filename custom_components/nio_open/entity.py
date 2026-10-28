"""Base entity for the NIO Open Platform."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VIN, DOMAIN
from .coordinator import NioCoordinator


def get_path(data: dict[str, Any] | None, path: str) -> Any:
    """Read a dotted path from nested dicts, returning None if missing."""
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


class NioEntity(CoordinatorEntity[NioCoordinator]):
    """Entity bound to one endpoint of the vehicle."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NioCoordinator, endpoint: str, key: str) -> None:
        super().__init__(coordinator)
        vin = coordinator.config_entry.data[CONF_VIN]
        self._endpoint = endpoint
        self._attr_unique_id = f"{vin}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vin)}, manufacturer="NIO", name=f"NIO {vin[-6:]}"
        )

    def _value(self, path: str) -> Any:
        return get_path(self.coordinator.data.get(self._endpoint), path)

    @property
    def available(self) -> bool:
        return super().available and self._endpoint in self.coordinator.data
