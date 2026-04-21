"""
Inicializa la base de datos.

Uso:
    python init_db.py

Efectos:
    1. Crea todas las tablas declaradas en los modelos (idempotente).
    2. Crea el usuario administrador leyendo ADMIN_USER y ADMIN_PASSWORD
       desde las variables de entorno.

Política de seguridad:
    - Si ADMIN_USER o ADMIN_PASSWORD faltan, el script aborta con código 1
      y mensaje claro. NUNCA se crea un admin con credenciales por defecto
      (evita "admin/admin" en producción por descuido).
    - Si el admin ya existe, no se duplica ni se sobreescribe la contraseña.
"""
from __future__ import annotations

import os
import sys

from app import create_app
from app.extensions import db
from app.models import User


def _abort(message: str) -> None:
    print(f"[init_db] ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    admin_user = os.environ.get("ADMIN_USER", "").strip()
    admin_password = os.environ.get("ADMIN_PASSWORD", "")

    if not admin_user or not admin_password:
        _abort(
            "ADMIN_USER y ADMIN_PASSWORD son obligatorias. "
            "Configura ambas antes de ejecutar init_db.py. "
            "No se crearán credenciales por defecto."
        )

    # Higiene mínima: exigir que la contraseña tenga una longitud razonable
    # antes de persistirla. Mitiga el caso de env mal configurada con "1".
    if len(admin_password) < 10:
        _abort("ADMIN_PASSWORD debe tener al menos 10 caracteres.")

    app = create_app()
    with app.app_context():
        db.create_all()
        print("[init_db] Tablas creadas (o ya existentes).")

        existing = User.query.filter_by(username=admin_user).first()
        if existing:
            print(
                f"[init_db] Usuario '{admin_user}' ya existe — no se modifica. "
                "Si necesitas rotar la contraseña, hazlo desde un script "
                "explícito o desde la UI."
            )
            return

        admin = User(username=admin_user, is_active=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"[init_db] Usuario administrador '{admin_user}' creado.")


if __name__ == "__main__":
    main()
