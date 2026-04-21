"""
Instancias singleton de extensiones Flask.

Se declaran aquí (sin `app`) para evitar imports circulares: los modelos,
formularios y blueprints importan desde este módulo, y `create_app()` las
enlaza a la aplicación en tiempo de arranque.
"""
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()
talisman = Talisman()

# Key function por IP remota (respeta X-Forwarded-For cuando la app corre
# detrás del proxy de Render/Nginx — configuramos ProxyFix en create_app).
limiter = Limiter(key_func=get_remote_address)

# Configuración de Flask-Login.
login_manager.login_view = "auth.login"
login_manager.login_message = "Debes iniciar sesión para acceder a esta página."
login_manager.login_message_category = "warning"
login_manager.session_protection = "strong"
