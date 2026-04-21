"""
Formularios de autenticación.

Flask-WTF añade automáticamente el token CSRF a cada form, validado en cada
POST. Si el token falta o es inválido, la petición falla con 400 — mitiga
CSRF contra el endpoint de login.
"""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField(
        "Usuario",
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={"autocomplete": "username", "autofocus": True},
    )
    password = PasswordField(
        "Contraseña",
        validators=[DataRequired(), Length(min=8, max=256)],
        render_kw={"autocomplete": "current-password"},
    )
    submit = SubmitField("Entrar")
