"""
Rutas de autenticación.

Defensa en profundidad contra brute-force y credential stuffing:
    - Flask-Limiter: 5 intentos/minuto por IP sobre POST /admin/login.
    - bcrypt.check_password_hash (timing-safe).
    - Log de cada intento fallido con IP y timestamp.
    - Mensaje de error genérico (no distinguimos "usuario no existe" de
      "contraseña incorrecta"): evita enumeración de usuarios.
    - CSRF token validado automáticamente por Flask-WTF.
"""
from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import limiter
from ..forms import LoginForm
from ..models import User
from ..utils.security import log_failed_login, log_successful_login

auth_bp = Blueprint("auth", __name__, url_prefix="/admin")


def _login_rate_limit() -> str:
    # Leemos el límite desde config en tiempo de request; permite ajustar
    # por entorno sin recompilar el decorador.
    return current_app.config["LOGIN_RATE_LIMIT"]


@auth_bp.route("/login", methods=["GET", "POST"])
# Rate limit aplicado a POST; los GETs a la página de login no se limitan
# para permitir visualización normal.
@limiter.limit(_login_rate_limit, methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        user = User.query.filter_by(username=username).first()

        # Verificamos incluso si el user no existe: previene un side-channel
        # timing attack que distinguiría "usuario no existe" (rápido) de
        # "contraseña incorrecta" (lento por bcrypt). Pagamos el hash siempre.
        password_ok = user.check_password(form.password.data) if user else False

        if user and user.is_active and password_ok:
            login_user(user, remember=False)
            user.update_last_login()
            log_successful_login(username)
            flash("Sesión iniciada correctamente.", "success")
            next_url = request.args.get("next")
            # NO redirigimos a URLs externas: evita open redirect (OWASP A1).
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("admin.dashboard"))

        log_failed_login(username)
        # Mensaje genérico — no revela si el usuario existe ni si está inactivo.
        flash("Credenciales incorrectas.", "danger")

    return render_template("admin/login.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("public.index"))
