"""
Rutas públicas: landing + API de proyectos + servido seguro de uploads.

Principios:
    - La landing renderiza el CV estático desde app/content.py.
    - Los proyectos NO se hardcodean en HTML: el template deja el contenedor
      vacío y main.js pide /api/projects y pinta. Esto garantiza que la
      galería siempre refleja la DB.
    - La respuesta API solo expone campos públicos (to_public_dict).
    - Uploads se sirven con send_from_directory + regex estricto sobre
      <filename>: bloquea path traversal y acceso a archivos arbitrarios.
"""
from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    render_template,
    request,
    send_from_directory,
)

from ..content import CV
from ..models import Project
from ..utils.file_handler import SAFE_FILENAME_RE

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    """Landing: hero, CV, portafolio (galería se hidrata vía fetch)."""
    # Precargamos destacados para evitar que la galería aparezca vacía si JS
    # está deshabilitado o tarda en ejecutarse (mejora SEO y accesibilidad).
    featured = (
        Project.query.filter_by(is_published=True, is_featured=True)
        .order_by(Project.sort_order.desc(), Project.created_at.desc())
        .limit(6)
        .all()
    )
    return render_template(
        "index.html",
        cv=CV,
        featured_projects=[p.to_public_dict() for p in featured],
    )


@public_bp.get("/api/projects")
def list_projects():
    """
    Lista proyectos publicados. Filtro opcional: ?category=...
    El filtro se aplica vía ORM (parámetro bindeado) → sin riesgo de SQLi.
    """
    query = Project.query.filter_by(is_published=True)

    category = request.args.get("category", "").strip()
    if category:
        query = query.filter(Project.category == category)

    projects = query.order_by(
        Project.is_featured.desc(),
        Project.sort_order.desc(),
        Project.created_at.desc(),
    ).all()

    return jsonify(
        {
            "projects": [p.to_public_dict() for p in projects],
            "categories": sorted(
                {
                    p.category
                    for p in Project.query.filter_by(is_published=True)
                    if p.category
                }
            ),
        }
    )


@public_bp.get("/api/projects/<int:project_id>")
def get_project(project_id: int):
    project = Project.query.filter_by(
        id=project_id, is_published=True
    ).first_or_404()
    return jsonify(project.to_public_dict())


@public_bp.get("/uploads/<path:filename>")
def serve_upload(filename: str):
    """
    Sirve imágenes subidas por el admin.
    Validamos el filename contra un regex estricto (hex32 + ext whitelisted)
    antes de pasarlo a send_from_directory → defensa en profundidad contra
    path traversal aun si el caller escapara Flask's URL routing.
    """
    if not SAFE_FILENAME_RE.match(filename):
        abort(404)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename,
        max_age=60 * 60 * 24,  # 1 día de cache en navegador
    )
