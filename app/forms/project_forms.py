"""
Formularios del CRUD de proyectos.

La validación server-side aquí es la autoridad; la validación client-side en
Bootstrap es solo UX. Nunca confiamos en lo que llega del cliente.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    IntegerField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    URL,
    DataRequired,
    Length,
    NumberRange,
    Optional,
)


class ProjectForm(FlaskForm):
    title = StringField(
        "Título",
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    description = TextAreaField(
        "Descripción",
        validators=[Optional(), Length(max=5000)],
    )
    category = StringField(
        "Categoría",
        validators=[Optional(), Length(max=60)],
        description="Ej: Auditoría, IA, Tributario",
    )
    # FileAllowed reemplaza el check de extensión a mano; el chequeo REAL de
    # tipo (magic bytes) ocurre en utils/file_handler.py.
    image = FileField(
        "Imagen (PNG, JPG, JPEG, WEBP — máx. 2 MB)",
        validators=[
            Optional(),
            FileAllowed(
                ["png", "jpg", "jpeg", "webp"],
                "Solo se permiten imágenes PNG, JPG, JPEG o WEBP.",
            ),
        ],
    )
    project_url = StringField(
        "URL del proyecto",
        validators=[Optional(), URL(require_tld=True), Length(max=512)],
    )
    tags = StringField(
        "Tags (separados por coma)",
        validators=[Optional(), Length(max=255)],
    )
    is_featured = BooleanField("Destacado")
    is_published = BooleanField("Publicado", default=True)
    sort_order = IntegerField(
        "Orden (mayor = primero)",
        validators=[Optional(), NumberRange(min=-10_000, max=10_000)],
        default=0,
    )
    submit = SubmitField("Guardar")


class DeleteForm(FlaskForm):
    """Form vacío cuya única función es vehicular el token CSRF del delete."""

    submit = SubmitField("Eliminar")
