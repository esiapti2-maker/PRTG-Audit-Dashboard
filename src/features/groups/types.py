from dataclasses import dataclass, field
from typing import List


@dataclass
class GroupRecord:
    """Representa un grupo (probe/group) de PRTG."""
    objid: int
    name: str
    parentid: int
    probe: str
    device_count: int
    sensor_count: int
    status: str
    # Hallazgos de auditoría
    has_no_devices: bool = False
    has_no_sensors: bool = False
    is_paused: bool = False
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ID": self.objid,
            "Nombre": self.name,
            "ID Padre": self.parentid,
            "Probe": self.probe,
            "Dispositivos": self.device_count,
            "Sensores": self.sensor_count,
            "Estado": self.status,
            "Sin Dispositivos": self.has_no_devices,
            "Sin Sensores": self.has_no_sensors,
            "Pausado": self.is_paused,
            "Tags": ", ".join(self.tags),
        }
