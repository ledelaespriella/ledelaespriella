"""
Configuración por entorno.

Se selecciona con la variable FLASK_ENV (development|production). La app aborta
al arrancar si SECRET_KEY no está definida o es débil: mitiga secuestro de
sesión y falsificación de tokens CSRF cuando una clave adivinable se filtra.
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
UPLOADS_DIR = INSTANCE_DIR / "uploads"

# Cargamos .env lo antes posible para que todos los módulos vean las vars.
load_dotenv(BASE_DIR / ".env")


def _normalize_database_url(url: str) -> str:
    # Render y Heroku históricamente entregan "postgres://", pero SQLAlchemy 2.x
    # rechaza ese dialect y exige "postgresql://". Normalizamos en un solo sitio.
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _require_secret_key() -> str:
    key = os.environ.get("SECRET_KEY", "")
    # 32 bytes = 64 hex chars. Cualquier valor más corto se trata como ausente:
    # evita que un desarrollador deje un placeholder débil por accidente.
    if len(key) < 32:
        raise RuntimeError(
            "SECRET_KEY no definida o demasiado corta (mínimo 32 bytes). "
            "Genera una con: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return key


class BaseConfig:
    """Valores compartidos por todos los entornos."""

    SECRET_KEY = _require_secret_key()

    # --- Base de datos ---------------------------------------------------
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'portfolio.db'}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads ---------------------------------------------------------
    # Mantenemos uploads fuera de /static para no exponer el directorio
    # directamente por el webserver; se sirven por ruta controlada.
    UPLOAD_FOLDER = str(UPLOADS_DIR)
    # 2 MB: mitiga DoS por subida de archivos grandes.
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # --- Sesiones / cookies ---------------------------------------------
    # HttpOnly impide que JS lea la cookie (mitiga XSS → session theft).
    SESSION_COOKIE_HTTPONLY = True
    # SameSite=Lax mitiga CSRF en peticiones top-level cross-site.
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", "60"))
    )

    # --- CSRF ------------------------------------------------------------
    WTF_CSRF_TIME_LIMIT = 3600  # 1h, obliga a refrescar tokens viejos

    # --- Rate limit ------------------------------------------------------
    LOGIN_RATE_LIMIT = os.environ.get("LOGIN_RATE_LIMIT", "5 per minute")
    # Default permisivo para el resto de rutas; las sensibles se anotan.
    RATELIMIT_DEFAULT = "200 per minute"
    RATELIMIT_STORAGE_URI = "memory://"

    # --- Logging ---------------------------------------------------------
    LOG_LEVEL = "INFO"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # En dev NO forzamos Secure para permitir HTTP local en localhost.
    SESSION_COOKIE_SECURE = False
    TALISMAN_FORCE_HTTPS = False
    LOG_LEVEL = "DEBUG"


class ProductionConfig(BaseConfig):
    DEBUG = False
    # Cookies solo por HTTPS: mitiga robo de sesión en MITM.
    SESSION_COOKIE_SECURE = True
    TALISMAN_FORCE_HTTPS = True
    # En prod requerimos Postgres explícito; fallar rápido si no está.
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError(
            "DATABASE_URL es obligatoria en producción (no usar SQLite por "
            "filesystem efímero en Render/Railway)."
        )


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development").lower()
    return CONFIG_BY_NAME.get(env, DevelopmentConfig)
