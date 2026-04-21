"""
Modelo Project.

Cada proyecto del portafolio. Todos los accesos SQL pasan por SQLAlchemy ORM
(nunca f-strings en SQL) → mitiga inyección. `to_public_dict()` omite campos
internos como `is_published` que no deberían filtrarse por la API pública.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index

from ..extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # Ej: "Auditoría", "IA", "Tributario". Sin tabla aparte para simplicidad;
    # la UI descubre las categorías disponibles agrupando los valores existentes.
    category = db.Column(db.String(60), nullable=True, index=True)
    # Guardamos SOLO el nombre de archivo (UUID + ext). La ruta la construye
    # la vista /uploads/<filename> — así podemos migrar a S3 sin tocar datos.
    image_filename = db.Column(db.String(255), nullable=True)
    project_url = db.Column(db.String(512), nullable=True)
    # CSV simple (evita segunda tabla); el frontend hace split(",").
    tags = db.Column(db.String(255), nullable=True)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    # Permite ocultar sin borrar → historial auditable; el admin puede re-publicar.
    is_published = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Índice compuesto: acelera el listing público más frecuente.
    __table_args__ = (
        Index("ix_project_published_order", "is_published", "sort_order"),
    )

    # --- Serialización ------------------------------------------------------

    def _tags_list(self) -> list[str]:
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def to_dict(self) -> dict:
        """Vista completa para el panel admin (incluye campos internos)."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "image_filename": self.image_filename,
            "project_url": self.project_url,
            "tags": self._tags_list(),
            "is_featured": self.is_featured,
            "is_published": self.is_published,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_public_dict(self) -> dict:
        """Vista filtrada para la API pública: omite estado interno."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "image_filename": self.image_filename,
            "project_url": self.project_url,
            "tags": self._tags_list(),
            "is_featured": self.is_featured,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Project {self.id} {self.title!r}>"
