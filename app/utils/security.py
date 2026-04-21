"""
Helpers de seguridad reutilizables.
"""
from __future__ import annotations

from datetime import datetime

from flask import current_app, request


def log_failed_login(username: str) -> None:
    """
    Registra un intento de login fallido con IP y timestamp.
    Útil para detectar ataques de fuerza bruta aun cuando Flask-Limiter
    ya los esté mitigando. No registramos la contraseña intentada.
    """
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?")
    current_app.logger.warning(
        "Login fallido: usuario=%r ip=%s ts=%s ua=%r",
        username,
        ip.split(",")[0].strip(),  # toma la primera IP (la original del cliente)
        datetime.utcnow().isoformat(),
        request.headers.get("User-Agent", "?")[:200],
    )


def log_successful_login(username: str) -> None:
    """Contraparte del anterior para disponer de una auditoría completa."""
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?")
    current_app.logger.info(
        "Login exitoso: usuario=%r ip=%s ts=%s",
        username,
        ip.split(",")[0].strip(),
        datetime.utcnow().isoformat(),
    )
