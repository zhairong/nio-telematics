"""Sensors for the NIO Open Platform."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NioConfigEntry
from .entity import NioEntity

MEASURE = SensorStateClass.MEASUREMENT


@dataclass(frozen=True, kw_only=True)
class NioSensorDescription(SensorEntityDescription):
    """Sensor reading `path` of `endpoint`."""

    endpoint: str
    path: str
    offset: int = 0


def _d(endpoint, path, name, *, cls=None, unit=None, state=None, enabled=True, offset=0):
    # `name` documents the entity at each call site; the display name itself
    # comes from `translations/*.json` via `translation_key` (see strings.json).
    key = f"{endpoint}_{path.replace('.', '_')}"
    return NioSensorDescription(
        key=key,
        translation_key=key,
        endpoint=endpoint,
        path=path,
        offset=offset,
        device_class=cls,
        native_unit_of_measurement=unit,
        state_class=state,
        entity_registry_enabled_default=enabled,
    )


BATTERY = SensorDeviceClass.BATTERY
TEMP = SensorDeviceClass.TEMPERATURE
VOLT = SensorDeviceClass.VOLTAGE
AMP = SensorDeviceClass.CURRENT
DIST = SensorDeviceClass.DISTANCE
CELSIUS = UnitOfTemperature.CELSIUS
SEATS = (
    ("frnt_le", "Front left"),
    ("frnt_ri", "Front right"),
    ("re_le", "Rear left"),
    ("re_ri", "Rear right"),
)

SENSORS: tuple[NioSensorDescription, ...] = (
    _d("soc_status", "soc", "Battery", cls=BATTERY, unit=PERCENTAGE, state=MEASURE),
    _d("soc_status", "remaining_range", "Remaining range", cls=DIST, unit=UnitOfLength.KILOMETERS, state=MEASURE),
    _d("soc_status", "chrg_state", "Charging state"),
    _d("soc_status", "chrg_final_soc", "Charge target", unit=PERCENTAGE, state=MEASURE),
    _d("soc_status", "max_soc", "Maximum SOC limit", unit=PERCENTAGE, state=MEASURE),
    _d("soc_status", "dump_enrgy", "Discharged energy", cls=SensorDeviceClass.ENERGY, unit=UnitOfEnergy.KILO_WATT_HOUR, state=SensorStateClass.TOTAL, enabled=False),
    _d("soc_status", "hivolt_btry_curnt", "Battery current", cls=AMP, unit=UnitOfElectricCurrent.AMPERE, state=MEASURE),
    _d("soc_status", "sin_btry_hist_temp", "Highest cell temperature", cls=TEMP, unit=CELSIUS, state=MEASURE, enabled=False, offset=-40),
    _d("soc_status", "sin_btry_lwst_temp", "Lowest cell temperature", cls=TEMP, unit=CELSIUS, state=MEASURE, enabled=False, offset=-40),
    _d("soc_status", "soc_v2lstatus", "V2L status", enabled=False),
    _d("vehicle_status", "speed", "Speed", cls=SensorDeviceClass.SPEED, unit=UnitOfSpeed.KILOMETERS_PER_HOUR, state=MEASURE),
    _d("vehicle_status", "mileage", "Odometer", cls=DIST, unit=UnitOfLength.KILOMETERS, state=SensorStateClass.TOTAL_INCREASING),
    _d("vehicle_status", "vehl_state", "Vehicle state"),
    _d("vehicle_status", "chrg_state", "Vehicle charging state", enabled=False),
    _d("vehicle_status", "oprtn_mode", "Operation mode", enabled=False),
    _d("vehicle_status", "vehl_totl_volt", "Battery voltage", cls=VOLT, unit=UnitOfElectricPotential.VOLT, state=MEASURE),
    _d("vehicle_status", "vehl_totl_curnt", "Vehicle current", cls=AMP, unit=UnitOfElectricCurrent.AMPERE, state=MEASURE, enabled=False),
    _d("vehicle_status", "gear", "Gear", enabled=False),
    _d("position_status", "heading", "Heading", unit="°", state=MEASURE, enabled=False),
    _d("hvac_status", "amb_temp_c", "Ambient temperature", cls=TEMP, unit=CELSIUS, state=MEASURE),
    _d("hvac_status", "outside_temp_c", "Outside temperature", cls=TEMP, unit=CELSIUS, state=MEASURE),
    _d("hvac_status", "pm2p5cabin", "Cabin PM2.5", cls=SensorDeviceClass.PM25, unit="µg/m³", state=MEASURE),
    _d("fridge_status", "fridge_set_temp", "Fridge target temperature", cls=TEMP, unit=CELSIUS, state=MEASURE),
    _d("fridge_status", "fridge_mod_sts", "Fridge mode"),
    _d("extremum_data", "highest_temp", "Highest battery temperature", cls=TEMP, unit=CELSIUS, state=MEASURE),
    _d("extremum_data", "lowest_temp", "Lowest battery temperature", cls=TEMP, unit=CELSIUS, state=MEASURE),
    _d("extremum_data", "sin_btry_hist_volt", "Highest cell voltage", cls=VOLT, unit=UnitOfElectricPotential.VOLT, state=MEASURE, enabled=False),
    _d("extremum_data", "sin_btry_lwst_volt", "Lowest cell voltage", cls=VOLT, unit=UnitOfElectricPotential.VOLT, state=MEASURE, enabled=False),
    _d("driving_data", "vcu_drvg_mod", "Driving mode"),
    _d("driving_data", "average_speed", "Average speed", cls=SensorDeviceClass.SPEED, unit=UnitOfSpeed.KILOMETERS_PER_HOUR, state=MEASURE, enabled=False),
    _d("driving_data", "aclrtn_pedal_posn", "Accelerator pedal", unit=PERCENTAGE, state=MEASURE, enabled=False),
    _d("trip_status", "trip_odometer", "Trip distance", cls=DIST, unit=UnitOfLength.KILOMETERS, state=MEASURE),
    _d("trip_status", "trip_eng", "Trip energy", cls=SensorDeviceClass.ENERGY, unit=UnitOfEnergy.KILO_WATT_HOUR, state=SensorStateClass.TOTAL),
    _d("heating_status", "steer_wheel_heat_sts", "Steering wheel heating"),
    _d("heating_status", "hv_batt_pre_sts", "Battery preheating"),
    *(
        _d("heating_status", f"seat_heat_{p}_sts", f"{label} seat heating")
        for p, label in SEATS
    ),
    *(
        _d("heating_status", f"seat_vent_{p}_sts", f"{label} seat ventilation")
        for p, label in SEATS
    ),
    *(
        _d("window_status", f"window_positions.win_{p}_posn", f"{label} window position", unit=PERCENTAGE, state=MEASURE)
        for p, label in SEATS
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: NioConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up NIO sensors."""
    coordinator = entry.runtime_data
    async_add_entities(NioSensor(coordinator, d) for d in SENSORS)


class NioSensor(NioEntity, SensorEntity):
    """A NIO telemetry value."""

    entity_description: NioSensorDescription

    def __init__(self, coordinator, description: NioSensorDescription) -> None:
        super().__init__(coordinator, description.endpoint, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        value = self._value(self.entity_description.path)
        if not self.entity_description.offset:
            return value
        # Offset-encoded values: 0 means unsampled, 0xFE/0xFF are error sentinels.
        if not isinstance(value, (int, float)) or not 0 < value < 0xFE:
            return None
        return value + self.entity_description.offset
