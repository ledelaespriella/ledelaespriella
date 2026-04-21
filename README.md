# Portafolio — Luis Eduardo De la Espriella Jiménez

Portafolio web profesional del Contador Público y consultor financiero
Luis Eduardo De la Espriella Jiménez. Aplicación Flask modular con panel
de administración protegido, galería de proyectos filtrable y API REST,
diseñada para desplegarse en producción sin refactor.

## Stack

- **Backend**: Flask 3 (factory pattern), SQLAlchemy 2, Flask-Login,
  Flask-WTF (CSRF), Flask-Limiter (rate limit), Flask-Talisman (CSP +
  cabeceras de seguridad), Flask-Bcrypt (hash de contraseñas).
- **Frontend**: Bootstrap 5 por CDN + CSS propio (paleta cian `#00AEEF`
  / negro `#1A1A1A`, tipografías Trebuchet MS y Calibri), JavaScript
  vanilla ES6+ (IntersectionObserver, fetch), sin jQuery ni SPAs.
- **DB**: SQLite en desarrollo, PostgreSQL en producción (mismo ORM).
- **Servidor**: Gunicorn detrás de Nginx (VPS) o del proxy de Render/Railway.

## Estructura

```
.
├── app/
│   ├── __init__.py            # create_app()
│   ├── extensions.py          # instancias singleton
│   ├── content.py             # contenido estático del CV
│   ├── models/ (user, project)
│   ├── routes/ (public, auth, admin)
│   ├── forms/  (auth, project)
│   ├── utils/  (file_handler, security)
│   ├── templates/ (base, index, admin/*, 403/404/500)
│   └── static/ (css/custom.css, js/main.js, js/admin.js)
├── config.py                  # BaseConfig / Dev / Prod
├── init_db.py                 # crea tablas + admin desde env
├── run.py                     # entrypoint WSGI
├── requirements.txt
├── Procfile                   # web: gunicorn ...
├── runtime.txt                # python-3.12.3
├── .env.example
├── deploy/
│   ├── nginx.conf.example
│   └── portfolio.service
└── README.md
```

## Instalación local (paso a paso)

```bash
# 1. Clonar el repo
git clone https://github.com/ledelaespriella/ledelaespriella.git
cd ledelaespriella

# 2. Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configurar el entorno
cp .env.example .env
# Genera una SECRET_KEY fuerte y pégala en .env:
python -c "import secrets; print(secrets.token_hex(32))"
# Edita .env y completa ADMIN_USER y ADMIN_PASSWORD (mínimo 10 caracteres).

# 4. Inicializar la base de datos y crear el admin
python init_db.py

# 5. Arrancar el servidor de desarrollo
flask --app run run
# o bien: python run.py
```

Abre http://localhost:5000 (sitio público) y http://localhost:5000/admin/login
(panel de administración).

## Despliegue en Render

1. **Crea una base de datos PostgreSQL** en Render y copia la `Internal Database URL`.
2. **Crea un Web Service** apuntando a este repositorio.
3. Configura los comandos:
   - **Build command**: `pip install -r requirements.txt && python init_db.py`
   - **Start command**: `gunicorn --workers 3 --bind 0.0.0.0:$PORT run:app`
   - **Runtime**: `Python 3.12`
4. Añade las variables de entorno en *Environment*:

   | Variable | Valor |
   |----------|-------|
   | `FLASK_ENV` | `production` |
   | `SECRET_KEY` | generar con `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `DATABASE_URL` | URL Postgres del paso 1 (Render sustituye automáticamente `postgres://`; la app normaliza a `postgresql://`) |
   | `ADMIN_USER` | tu usuario admin |
   | `ADMIN_PASSWORD` | contraseña fuerte (≥ 10 caracteres) |
   | `SESSION_LIFETIME_MINUTES` | `60` (opcional) |
   | `LOGIN_RATE_LIMIT` | `5 per minute` (opcional) |

5. Despliega. El *build command* ejecuta `init_db.py` que crea las tablas y
   siembra el administrador. En deploys posteriores, `init_db.py` es
   idempotente: no duplica ni sobreescribe credenciales.

6. **Persistencia de uploads**: Render tiene filesystem efímero. Para
   conservar imágenes entre deploys, conecta un [Render Disk](https://render.com/docs/disks)
   a `/opt/render/project/src/instance/uploads` o migra a S3/R2.

## Despliegue en Railway

Similar a Render:

1. Añade un servicio PostgreSQL y pega su `DATABASE_URL`.
2. Configura las mismas variables de entorno.
3. Railway detecta `Procfile` automáticamente.
4. Añade un Volumen montado en `/app/instance/uploads` para persistir subidas.

## Despliegue en VPS (Nginx + Gunicorn)

1. Clona el repo en `/srv/portafolio` bajo un usuario sin privilegios (`portfolio`).
2. Crea `.venv` e instala dependencias como ese usuario.
3. Crea `/etc/portfolio.env` con las mismas variables (chmod 600, owner portfolio).
4. Copia `deploy/portfolio.service` a `/etc/systemd/system/` y habilita:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now portfolio
   ```
5. Copia `deploy/nginx.conf.example` a `/etc/nginx/sites-available/portafolio.conf`,
   ajusta el dominio, enlaza a `sites-enabled/` y recarga Nginx.
6. Ejecuta Certbot para HTTPS:
   ```bash
   sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
   ```

## Checklist de seguridad pre-lanzamiento

Antes de exponer la app a internet, verifica:

- [ ] `FLASK_ENV=production` y `DEBUG` es `False` (Flask-Talisman fuerza HTTPS).
- [ ] `SECRET_KEY` generada con `secrets.token_hex(32)` (≥ 32 bytes).
- [ ] `SESSION_COOKIE_SECURE=True` en producción (lo hace `ProductionConfig`).
- [ ] `DATABASE_URL` apunta a PostgreSQL gestionado, no a SQLite.
- [ ] `ADMIN_PASSWORD` fuerte, nunca `admin/admin` ni similar.
- [ ] `init_db.py` ejecutado una vez; no commitear el `.db` local.
- [ ] HTTPS activo (Certbot o SSL del hosting); Nginx fuerza redirección 80→443.
- [ ] `curl -I https://tu-dominio.com/` muestra: `Strict-Transport-Security`,
      `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
      `Referrer-Policy: strict-origin-when-cross-origin`,
      `Content-Security-Policy: default-src 'self'; ...`.
- [ ] Rate limit operativo: 6 logins fallidos seguidos devuelven `429 Too Many Requests`.
- [ ] Upload de archivo no-imagen renombrado a `.png` se rechaza (magic bytes).
- [ ] Upload > 2 MB devuelve `413 Request Entity Too Large`.
- [ ] Request a `/uploads/../config.py` responde `404`.
- [ ] POST a `/admin/project/new` sin `csrf_token` responde `400 Bad Request`.
- [ ] Logs en consola/Render/systemd incluyen intentos de login con IP.
- [ ] `.env` fuera de git (`git check-ignore .env` devuelve `.env`).
- [ ] Backups de la DB configurados (Render lo hace automáticamente en el plan free).

## Desarrollo

Los proyectos se crean desde `/admin`. La galería pública los sirve vía
`GET /api/projects`; el frontend los renderiza con `document.createElement`
y `textContent` (nunca `innerHTML` con datos externos).

El CV (presentación, experiencia, habilidades, educación) vive en
`app/content.py`. Editar allí y desplegar.

## Licencia

Contenido personal. Código disponible para referencia y aprendizaje.
