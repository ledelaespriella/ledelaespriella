"""
Panel de administración (CRUD de proyectos).

Todas las rutas requieren sesión activa (@login_required). Mutaciones por
formulario usan CSRF (Flask-WTF). Las mutaciones por fetch (PATCH para
toggles) envían el token por header X-CSRFToken, validado por Flask-WTF
cuando CSRFProtect intercepta el request.
"""
from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from ..extensions import db
from ..forms import DeleteForm, ProjectForm
from ..models import Project
from ..utils.file_handler import (
    InvalidImageError,
    delete_uploaded_image,
    save_uploaded_image,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Tamaño de página del dashboard. Hardcodeado a propósito: no hay UX para que
# el admin lo cambie y evita un parámetro más para manipular en URLs.
PAGE_SIZE = 20


@admin_bp.get("/")
@login_required
def dashboard():
    page = max(1, request.args.get("page", type=int, default=1))
    pagination = (
        Project.query.order_by(
            Project.sort_order.desc(), Project.created_at.desc()
        ).paginate(page=page, per_page=PAGE_SIZE, error_out=False)
    )
    return render_template(
        "admin/dashboard.html",
        pagination=pagination,
        projects=pagination.items,
        delete_form=DeleteForm(),  # provee token CSRF para cada botón eliminar
    )


@admin_bp.route("/project/new", methods=["GET", "POST"])
@login_required
def new_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project()
        _apply_form_to_project(form, project)

        try:
            if form.image.data:
                project.image_filename = save_uploaded_image(form.image.data)
        except InvalidImageError as exc:
            flash(f"Imagen inválida: {exc}", "danger")
            return render_template(
                "admin/project_form.html", form=form, project=None
            )

        db.session.add(project)
        db.session.commit()
        flash("Proyecto creado.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/project_form.html", form=form, project=None)


@admin_bp.route("/project/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def edit_project(project_id: int):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)

    if form.validate_on_submit():
        _apply_form_to_project(form, project)

        if form.image.data:
            try:
                new_name = save_uploaded_image(form.image.data)
            except InvalidImageError as exc:
                flash(f"Imagen inválida: {exc}", "danger")
                return render_template(
                    "admin/project_form.html", form=form, project=project
                )
            # Solo al éxito borramos la anterior → evita perder la imagen si
            # la subida falla a mitad del flujo.
            old = project.image_filename
            project.image_filename = new_name
            delete_uploaded_image(old)

        db.session.commit()
        flash("Proyecto actualizado.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/project_form.html", form=form, project=project
    )


@admin_bp.post("/project/<int:project_id>/delete")
@login_required
def delete_project(project_id: int):
    # DeleteForm valida el token CSRF; si falla, Flask-WTF responde 400.
    form = DeleteForm()
    if not form.validate_on_submit():
        abort(400)

    project = Project.query.get_or_404(project_id)
    filename = project.image_filename
    db.session.delete(project)
    db.session.commit()
    delete_uploaded_image(filename)
    flash("Proyecto eliminado.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.patch("/project/<int:project_id>/toggle-featured")
@login_required
def toggle_featured(project_id: int):
    return _toggle_boolean_field(project_id, "is_featured")


@admin_bp.patch("/project/<int:project_id>/toggle-published")
@login_required
def toggle_published(project_id: int):
    return _toggle_boolean_field(project_id, "is_published")


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _apply_form_to_project(form: ProjectForm, project: Project) -> None:
    """Copia los campos (excepto image) del form al modelo."""
    project.title = form.title.data.strip()
    project.description = (form.description.data or "").strip() or None
    project.category = (form.category.data or "").strip() or None
    project.project_url = (form.project_url.data or "").strip() or None
    project.tags = (form.tags.data or "").strip() or None
    project.is_featured = bool(form.is_featured.data)
    project.is_published = bool(form.is_published.data)
    project.sort_order = int(form.sort_order.data or 0)


def _toggle_boolean_field(project_id: int, field: str):
    """
    Flip booleano vía PATCH desde el dashboard.
    CSRFProtect ya valida el header X-CSRFToken antes de que lleguemos aquí.
    Whitelisteamos el nombre de campo → no hay forma de modificar columnas
    arbitrarias aunque alguien manipule la URL.
    """
    if field not in {"is_featured", "is_published"}:
        abort(400)
    project = Project.query.get_or_404(project_id)
    setattr(project, field, not getattr(project, field))
    db.session.commit()
    return jsonify({"id": project.id, field: getattr(project, field)})
