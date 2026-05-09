"""
shared/logger.py
================
Logger de consola para la auditoría PRTG.
Imprime resumen ejecutivo con todos los hallazgos.
"""


class AuditLogger:
    """
    Imprime resúmenes y mensajes de progreso en consola.
    """

    @staticmethod
    def header(site_name: str, host: str):
        print(f"\n[PRTG-AUDIT] Iniciando auditoría de: {site_name} ({host})")
        print("-" * 55)

    @staticmethod
    def summary(site_name: str, results: dict):
        """
        Imprime resumen ejecutivo.

        Args:
            site_name: Nombre del sitio auditado
            results:   Dict con conteos por categoría
        """
        print(f"\n{'='*55}")
        print(f"  RESUMEN AUDITORÍA — {site_name}")
        print(f"{'='*55}")
        print(f"  Dispositivos totales       : {results.get('devices', 0)}")
        print(f"  Sensores CAÍDOS            : {results.get('sensors_down', 0)}")
        print(f"  Sensores en WARNING        : {results.get('sensors_warning', 0)}")
        print(f"  Sensores SIN UMBRALES      : {results.get('sensors_no_limits', 0)}")
        print(f"  Sensores PAUSADOS          : {results.get('sensors_paused', 0)}")
        print(f"  Usuarios                   : {results.get('users', 0)}")
        print(f"  Notificaciones PAUSADAS    : {results.get('notifications_paused', 0)}")
        print(f"{'='*55}")

    @staticmethod
    def multi_site_done(output_dir: str, reports: list):
        print(f"\n[PRTG-AUDIT] Auditoría multi-sitio completada.")
        print(f"  Reportes generados en: {output_dir}/")
        for r in reports:
            print(f"    - {r}")
