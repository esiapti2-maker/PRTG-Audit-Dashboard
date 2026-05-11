"""
Configuración centralizada del proyecto.
Lee variables desde .env usando python-dotenv.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv es opcional en entornos donde las vars ya están seteadas


@dataclass
class PRTGInstance:
    name: str
    host: str
    username: str
    passhash: str
    verify_ssl: bool = False
    timeout: int = 30


@dataclass
class AppConfig:
    # Proxy / API server
    proxy_host: str = field(default_factory=lambda: os.getenv("PROXY_HOST", "0.0.0.0"))
    proxy_port: int = field(default_factory=lambda: int(os.getenv("PROXY_PORT", "5000")))
    proxy_debug: bool = field(default_factory=lambda: os.getenv("PROXY_DEBUG", "false").lower() == "true")
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "change-me-in-production"))
    cors_origins: List[str] = field(default_factory=lambda: [
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")
    ])

    # Export
    export_dir: str = field(default_factory=lambda: os.getenv("EXPORT_DIR", "./reportes"))

    # PRTG default instance (usada por el proxy cuando no se manda en el body)
    default_prtg_host: str = field(default_factory=lambda: os.getenv("PRTG_HOST", ""))
    default_prtg_user: str = field(default_factory=lambda: os.getenv("PRTG_USER", ""))
    default_prtg_passhash: str = field(default_factory=lambda: os.getenv("PRTG_PASSHASH", ""))
    default_verify_ssl: bool = field(default_factory=lambda: os.getenv("PRTG_VERIFY_SSL", "false").lower() == "true")


config = AppConfig()
