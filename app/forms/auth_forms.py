"""
app/forms/auth_forms.py — WTForms + CSRF for registration and login.
Password policy enforced in the validator.
"""
import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, ValidationError, Regexp
)


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=32),
            Regexp(
                r"^[a-zA-Z0-9_]+$",
                message="Username may only contain letters, numbers, and underscores.",
            ),
        ],
    )
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=12, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")

    def validate_password(self, field: PasswordField) -> None:
        pwd = field.data
        errors = []
        if not re.search(r"[A-Z]", pwd):
            errors.append("one uppercase letter")
        if not re.search(r"[a-z]", pwd):
            errors.append("one lowercase letter")
        if not re.search(r"\d", pwd):
            errors.append("one digit")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", pwd):
            errors.append("one special character")
        if errors:
            raise ValidationError(
                f"Password must contain: {', '.join(errors)}."
            )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")
