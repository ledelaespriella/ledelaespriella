"""
Punto de entrada WSGI.

Uso local:
    flask --app run run          # Flask detecta la variable `app`
    # o
    python run.py                # arranca el servidor de desarrollo

Producción (Render / Railway / VPS):
    gunicorn --workers 3 --bind 0.0.0.0:$PORT run:app
"""
from app import create_app

app = create_app()


if __name__ == "__main__":
    # Solo para uso local. En producción usamos gunicorn (ver Procfile).
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
