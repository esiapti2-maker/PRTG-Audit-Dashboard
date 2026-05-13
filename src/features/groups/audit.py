"""
src/features/groups/audit.py
=============================
Auditoría de grupos y probes de PRTG.

Hallazgos detectados:
  - Grupos sin dispositivos (árbol vacío)
  - Grupos sin sensores (nodo intermedio sin monitoreo)
  - Grupos pausados (zona ciega de monitoreo)
  - Grupos con nombre genérico/default ("New Group", "Group")

La API de PRTG devuelve grupos con content=groups.
Cada grupo tiene: objid, name, parentid, probe, totalsens, totaldev, status.
"""

import logging
from typing import List, Dict, Any

from src.core.client import PRTGClient
from src.core.exceptions import PRTGAuthError, PRTGConnectionError
from .types import GroupRecord

log = logging.getLogger(__name__)

# Nombres genéricos que sugieren falta de personalización
_GENERIC_NAMES = {
    "new group", "group", "nuevo grupo", "grupo",
    "probe device", "probe", "local probe",
}


class GroupAudit:
    """
    Ejecuta la auditoría de grupos/probes PRTG.

    Uso:
        ga = GroupAudit(client)
        result = ga.run()
        # result.empty_groups   → grupos sin dispositivos
        # result.paused_groups  → grupos pausados
        # result.generic_names  → grupos con nombre genérico
        # result.all_groups     → todos los grupos
    """

    # Columnas solicitadas a la API
    _COLUMNS = "objid,name,parentid,probe,totalsens,totaldev,status,tags"

    def __init__(self, client: PRTGClient):
        self._client = client

    # ─── API ──────────────────────────────────────────────────────────────────

    def run(self) -> "GroupAuditResult":
        """Ejecuta todos los chequeos y devuelve un GroupAuditResult."""
        log.info("[GroupAudit] Obteniendo grupos de PRTG...")
        raw = self._fetch_groups()
        records = [self._parse(r) for r in raw]
        log.info("[GroupAudit] %d grupos encontrados", len(records))

        result = GroupAuditResult(
            all_groups=records,
            empty_groups=[r for r in records if r.has_no_devices],
            no_sensor_groups=[r for r in records if r.has_no_sensors],
            paused_groups=[r for r in records if r.is_paused],
            generic_names=[
                r for r in records
                if r.name.strip().lower() in _GENERIC_NAMES
            ],
        )

        log.info(
            "[GroupAudit] Resumen → total=%d  sin_dispositivos=%d  "
            "sin_sensores=%d  pausados=%d  nombres_genéricos=%d",
            len(result.all_groups),
            len(result.empty_groups),
            len(result.no_sensor_groups),
            len(result.paused_groups),
            len(result.generic_names),
        )
        return result

    # ─── Privado ──────────────────────────────────────────────────────────────

    def _fetch_groups(self) -> List[Dict[str, Any]]:
        try:
            data = self._client.get(
                "/api/table.json",
                {
                    "content": "groups",
                    "columns": self._COLUMNS,
                    "count": 5000,
                    "output": "json",
                },
            )
            return data.get("groups", [])
        except (PRTGAuthError, PRTGConnectionError):
            raise
        except Exception as exc:  # noqa: BLE001
            log.warning("[GroupAudit] Error obteniendo grupos: %s", exc)
            return []

    @staticmethod
    def _parse(raw: Dict[str, Any]) -> GroupRecord:
        device_count = int(raw.get("totaldev", raw.get("totaldev_raw", 0)) or 0)
        sensor_count = int(raw.get("totalsens", raw.get("totalsens_raw", 0)) or 0)
        status_raw = str(raw.get("status", "")).lower()
        tags_raw = raw.get("tags", "")
        tags = [t.strip() for t in str(tags_raw).split(",") if t.strip()] if tags_raw else []

        return GroupRecord(
            objid=int(raw.get("objid", 0)),
            name=raw.get("name", "(sin nombre)"),
            parentid=int(raw.get("parentid", 0)),
            probe=raw.get("probe", ""),
            device_count=device_count,
            sensor_count=sensor_count,
            status=raw.get("status", ""),
            has_no_devices=(device_count == 0),
            has_no_sensors=(sensor_count == 0),
            is_paused=("paused" in status_raw),
            tags=tags,
        )


# ─── Resultado ────────────────────────────────────────────────────────────────

from dataclasses import dataclass, field  # noqa: E402 (import after class)
from typing import List  # noqa: E402


@dataclass
class GroupAuditResult:
    """Contenedor de resultados de GroupAudit."""
    all_groups: List[GroupRecord] = field(default_factory=list)
    empty_groups: List[GroupRecord] = field(default_factory=list)
    no_sensor_groups: List[GroupRecord] = field(default_factory=list)
    paused_groups: List[GroupRecord] = field(default_factory=list)
    generic_names: List[GroupRecord] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.all_groups)

    @property
    def has_issues(self) -> bool:
        return bool(
            self.empty_groups
            or self.paused_groups
            or self.generic_names
        )
