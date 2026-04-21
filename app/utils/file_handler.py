"""
Validación y guardado seguro de imágenes subidas por el admin.

Controles aplicados (en este orden):
    1. Extensión del nombre contra whitelist  → rechaza `.exe`, `.php`, etc.
    2. Tamaño (MAX_CONTENT_LENGTH ya lo enforce Flask en el request level).
    3. **Magic bytes reales del archivo**    → rechaza ejecutables
       renombrados a .png. NUNCA confiamos en la extensión declarada.
    4. Renombrado con uuid4() hex            → evita colisiones, path
       traversal (../) y leakage del nombre original del cliente.

El archivo se guarda en UPLOAD_FOLDER (instance/uploads/), fuera de /static,
y se sirve por ruta controlada /uploads/<filename> con regex estricto.
"""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage

# Firmas de cabecera (magic bytes) — primeros bytes únicos por formato.
# Referencia: https://en.wikipedia.org/wiki/List_of_file_signatures
_MAGIC_BYTES = {
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    # WEBP: "RIFF....WEBP" — bytes 0-3 = RIFF, bytes 8-11 = WEBP
    "webp": [b"RIFF"],
}

# Nombre seguro para servir: SOLO hex32 + extensión de la whitelist.
# Se usa en la ruta /uploads/<filename> para bloquear path traversal.
SAFE_FILENAME_RE = re.compile(r"^[a-f0-9]{32}\.(png|jpg|jpeg|webp)$")


class InvalidImageError(ValueError):
    """La imagen subida no pasó la validación de tipo o tamaño."""


def _extract_extension(filename: str) -> str:
    # Usamos rsplit para tomar SOLO la última extensión, bloqueando trucos
    # tipo "foo.php.png" → extensión real php. Descartamos cualquier ruta.
    name = os.path.basename(filename)
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[1].lower()


def _validate_magic_bytes(file_storage: FileStorage, ext: str) -> bool:
    # Leemos solo lo necesario y rewind — no consumimos el stream.
    head = file_storage.stream.read(16)
    file_storage.stream.seek(0)

    if ext in {"png", "jpg", "jpeg"}:
        return any(head.startswith(sig) for sig in _MAGIC_BYTES[ext])
    if ext == "webp":
        # RIFF....WEBP: verificamos "RIFF" al inicio y "WEBP" en offset 8.
        return head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    return False


def save_uploaded_image(file_storage: FileStorage) -> str:
    """
    Valida y persiste una imagen. Devuelve el filename generado (solo nombre,
    sin ruta) para almacenar en la columna projects.image_filename.

    Lanza InvalidImageError si la imagen no cumple los controles.
    """
    if not file_storage or not file_storage.filename:
        raise InvalidImageError("No se recibió ningún archivo.")

    allowed = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    ext = _extract_extension(file_storage.filename)

    if ext not in allowed:
        raise InvalidImageError(
            f"Extensión '{ext}' no permitida. Solo: {', '.join(sorted(allowed))}."
        )

    if not _validate_magic_bytes(file_storage, ext):
        # El contenido del archivo NO corresponde a la extensión declarada.
        # Esto bloquea ataques tipo "exe renombrado a .png".
        raise InvalidImageError(
            "El contenido del archivo no coincide con su extensión."
        )

    # Normalizamos jpg/jpeg a una misma extensión en disco para simplicidad.
    stored_ext = "jpg" if ext == "jpeg" else ext
    safe_name = f"{uuid.uuid4().hex}.{stored_ext}"

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_storage.save(upload_dir / safe_name)
    return safe_name


def delete_uploaded_image(filename: str | None) -> None:
    """
    Borra una imagen previamente guardada. Silencioso si no existe, para
    que no falle al eliminar un proyecto cuya imagen ya fue quitada a mano.
    """
    if not filename or not SAFE_FILENAME_RE.match(filename):
        # Nombre no conforme → nos negamos a borrar nada (defensa contra
        # filename envenenado en DB).
        return
    target = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    try:
        target.unlink(missing_ok=True)
    except OSError as exc:  # pragma: no cover
        current_app.logger.warning("No pude borrar %s: %s", target, exc)
