"""
Modelo User.

Diseñado para un único administrador (o pocos); las contraseñas se guardan
exclusivamente como hash bcrypt con cost factor 12. Evitamos werkzeug.security
simple porque PBKDF2 por defecto es más débil que bcrypt ante ataque offline
con GPU.
"""
from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin

from ..extensions import bcrypt, db

# Cost factor 12 ≈ ~250 ms por hash en hardware moderno. Sube el costo al
# atacante sin degradar la UX del login único del admin.
BCRYPT_ROUNDS = 12


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    # 256 chars: bcrypt hashes son ~60, dejamos holgura por si se cambia algoritmo.
    password_hash = db.Column(db.String(256), nullable=False)
    # La columna sobrescribe la propiedad por defecto de UserMixin. Flask-Login
    # la consulta para autorizar sesiones → podemos revocar un admin sin borrarlo.
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )

    # --- Password handling --------------------------------------------------

    def set_password(self, plain_password: str) -> None:
        # Generamos el hash con cost 12 explícito; jamás almacenamos el plaintext.
        self.password_hash = bcrypt.generate_password_hash(
            plain_password, rounds=BCRYPT_ROUNDS
        ).decode("utf-8")

    def check_password(self, plain_password: str) -> bool:
        # bcrypt.check_password_hash es timing-safe; no reemplazar por == manual.
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, plain_password)

    # --- Helpers ------------------------------------------------------------

    def update_last_login(self) -> None:
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self) -> str:  # pragma: no cover - solo debug
        return f"<User {self.username!r}>"
