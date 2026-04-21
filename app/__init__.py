"""
Application factory.

Inicializa todas las extensiones, registra blueprints, configura la CSP
(Content Security Policy) y los handlers de errores. La factory permite
crear instancias aisladas para testing sin estado global.
"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from config import INSTANCE_DIR, UPLOADS_DIR, get_config

from .extensions import bcrypt, csrf, db, limiter, login_manager, talisman


def create_app(config_class=None) -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        instance_path=str(INSTANCE_DIR),
    )

    # Selección de config por entorno; permite override explícito en tests.
    app.config.from_object(config_class or get_config())

    # Asegura que el directorio de uploads exista; si no, falla al subir.
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # ProxyFix: hace que request.remote_addr refleje la IP real cuando
    # la app corre detrás de Nginx o el load balancer de Render. Sin esto,
    # el rate limiter vería la IP del proxy y limitaría a todos por igual.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _configure_logging(app)

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)

    # Content Security Policy: mitiga XSS restringiendo de dónde puede cargar
    # recursos el navegador. Permitimos jsdelivr (Bootstrap) y nuestros propios
    # assets. 'unsafe-inline' se habilita solo para estilos porque Bootstrap
    # inyecta algunos estilos inline; los scripts NO usan 'unsafe-inline'.
    csp = {
        "default-src": "'self'",
        "script-src": [
            "'self'",
            "https://cdn.jsdelivr.net",
        ],
        "style-src": [
            "'self'",
            "https://cdn.jsdelivr.net",
            "'unsafe-inline'",  # requerido por algunos componentes Bootstrap
        ],
        "font-src": [
            "'self'",
            "https://cdn.jsdelivr.net",
            "data:",
        ],
        "img-src": ["'self'", "data:"],
        "connect-src": "'self'",
        "frame-ancestors": "'none'",
        "base-uri": "'self'",
        "form-action": "'self'",
    }
    talisman.init_app(
        app,
        content_security_policy=csp,
        force_https=app.config.get("TALISMAN_FORCE_HTTPS", False),
        strict_transport_security=app.config.get("TALISMAN_FORCE_HTTPS", False),
        session_cookie_secure=app.config.get("SESSION_COOKIE_SECURE", False),
        referrer_policy="strict-origin-when-cross-origin",
        frame_options="DENY",
    )

    # Cabeceras extra que Talisman no cubre por defecto.
    @app.after_request
    def _security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return response

    # User loader de Flask-Login: import diferido para romper el ciclo.
    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        # int() es seguro: Flask-Login solo pasa strings desde la cookie firmada.
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None


def _register_blueprints(app: Flask) -> None:
    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(_err):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(_err):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(_err):
        # Alzado automáticamente cuando MAX_CONTENT_LENGTH se supera.
        return render_template("500.html", message="Archivo demasiado grande."), 413

    @app.errorhandler(500)
    def server_error(err):
        # Logueamos el stack completo en servidor, mostramos mensaje genérico.
        app.logger.exception("Error 500: %s", err)
        return render_template("500.html"), 500


def _configure_logging(app: Flask) -> None:
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"))
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Handler de stdout: lo capturan Render/Railway/systemd.
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    stream.setLevel(level)

    app.logger.handlers.clear()
    app.logger.addHandler(stream)
    app.logger.setLevel(level)

    # En desarrollo también escribimos a archivo para debugging offline.
    if app.debug:
        log_dir = Path(app.instance_path) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "app.log", maxBytes=1_000_000, backupCount=3
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        app.logger.addHandler(file_handler)
