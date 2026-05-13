"""
tests/conftest.py
==================
Configuración compartida de pytest.
Asegura que el directorio raíz esté en el path de Python para todos los tests.
"""

import sys
from pathlib import Path

# Agrega la raíz del proyecto al sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
