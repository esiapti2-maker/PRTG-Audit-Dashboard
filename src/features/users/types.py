from dataclasses import dataclass, field
from enum import Enum
from typing import List


class RiskLevel(str, Enum):
    """Nivel de riesgo asignado a una cuenta de usuario PRTG."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UserRecord:
    """Representa un usuario PRTG con metadatos de auditoría."""
    objid: int
    name: str
    email: str
    role: str                          # PRTG role string (e.g. 'Administrator')
    is_admin: bool
    is_readonly: bool
    last_login: str                    # ISO string o vacío si nunca ha ingresado
    active: bool
    groups: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    risk_reasons: List[str] = field(default_factory=list)

    @property
    def display_risk(self) -> str:
        return self.risk_level.value.upper()
