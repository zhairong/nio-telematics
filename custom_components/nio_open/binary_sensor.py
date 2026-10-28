"""Binary sensors for the NIO Open Platform."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NioConfigEntry
from .entity import NioEntity

OPENED = "AJAR_OPENED"
LOCKED = "LOCK_LOCKED"
LIGHT_ON = "LIGHT_ON"


@dataclass(frozen=True, kw_only=True)
class NioBinarySensorDescription(BinarySensorEntityDescription):
    """On when `path` of `endpoint` equals `on_value`; `invert` flips it.

    HA lock-class sensors are on when unlocked, hence `invert` for lock states.
    """

    endpoint: str
    path: str
    on_value: object = True
    invert: bool = False


def _d(endpoint, path, name, on_value, cls=None, invert=False, enabled=True):
    return NioBinarySensorDescription(
        key=f"{endpoint}_{path.replace('.', '_')}",
        name=name,
        endpoint=endpoint,
        path=path,
        on_value=on_value,
        invert=invert,
        device_class=cls,
        entity_registry_enabled_default=enabled,
    )


DOOR = BinarySensorDeviceClass.DOOR
LOCK = BinarySensorDeviceClass.LOCK
LIGHT = BinarySensorDeviceClass.LIGHT
DOORS = (
    ("frnt_le", "Front left"),
    ("frnt_ri", "Front right"),
    ("re_le", "Rear left"),
    ("re_ri", "Rear right"),
)

BINARY_SENSORS: tuple[NioBinarySensorDescription, ...] = (
    *(
        _d("door_status", f"door_ajars.door_ajar_{p}_sts", f"{label} door", OPENED, DOOR)
        for p, label in DOORS
    ),
    *(
        _d("door_status", f"door_locks.door_lock_{p}_sts", f"{label} door lock", LOCKED, LOCK, invert=True)
        for p, label in DOORS[:2]
    ),
    _d("door_status", "tailgate_status.ajar_status", "Tailgate", OPENED, DOOR),
    _d("door_status", "engine_hood_status.ajar_status", "Hood", OPENED, DOOR),
    _d("door_status", "vehicle_lock_status", "Vehicle lock", "FULLY_LOCKED", LOCK, invert=True),
    _d("light_status", "lo_beam_on", "Low beam", LIGHT_ON, LIGHT),
    _d("light_status", "head_light_on", "Headlight", LIGHT_ON, LIGHT),
    _d("light_status", "hi_beam_on", "High beam", LIGHT_ON, LIGHT),
    _d("hvac_status", "air_con_on", "Air conditioning", True),
    _d("hvac_status", "pm2p5filter_active", "PM2.5 filter", True, enabled=False),
    _d("vehicle_status", "urgt_prw_shtdwn", "Emergency power shutdown", True, BinarySensorDeviceClass.PROBLEM, enabled=False),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: NioConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up NIO binary sensors, plus charge ports (variable count)."""
    coordinator = entry.runtime_data
    entities = [NioBinarySensor(coordinator, d) for d in BINARY_SENSORS]
    entities.append(NioChargePortSensor(coordinator))
    async_add_entities(entities)


class NioBinarySensor(NioEntity, BinarySensorEntity):
    """A two-state NIO signal."""

    entity_description: NioBinarySensorDescription

    def __init__(self, coordinator, description: NioBinarySensorDescription) -> None:
        super().__init__(coordinator, description.endpoint, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        value = self._value(self.entity_description.path)
        if value is None:
            return None
        result = value == self.entity_description.on_value
        return not result if self.entity_description.invert else result


class NioChargePortSensor(NioEntity, BinarySensorEntity):
    """Open when any charge port is open."""

    _attr_name = "Charge port"
    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "door_status", "door_status_charge_port")

    @property
    def is_on(self) -> bool | None:
        ports = self._value("charge_port_status")
        if not isinstance(ports, list) or not ports:
            return None
        return any(p.get("ajar_status") == OPENED for p in ports)
