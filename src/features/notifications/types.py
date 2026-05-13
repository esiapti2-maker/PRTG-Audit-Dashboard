from dataclasses import dataclass, field
from typing import List


@dataclass
class NotificationRecord:
    """Representa una plantilla/acción de notificación PRTG."""
    objid: int
    name: str
    active: bool
    has_email: bool              # Tiene método de entrega Email configurado
    has_sms: bool                # Tiene método SMS
    has_exec: bool               # Ejecuta script/programa externo
    triggers_count: int          # Número de sensores/dispositivos que la usan como trigger
    schedule: str                # Horario de notificación (vacío = siempre)
    postpone: int                # Minutos de delay antes de disparar (0 = inmediato)
    subject: str                 # Asunto del email (si aplica)
    issues: List[str] = field(default_factory=list)  # Problemas detectados

    @property
    def is_orphan(self) -> bool:
        """Sin triggers activos — nunca se disparará."""
        return self.triggers_count == 0

    @property
    def has_delivery_method(self) -> bool:
        """Tiene al menos un método de entrega configurado."""
        return self.has_email or self.has_sms or self.has_exec
