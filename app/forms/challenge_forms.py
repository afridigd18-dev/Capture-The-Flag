"""
app/forms/challenge_forms.py — Flag submission and hint-unlock forms.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange


class FlagSubmitForm(FlaskForm):
    flag = StringField(
        "Flag",
        validators=[DataRequired(), Length(max=512)],
    )
    submit = SubmitField("Submit Flag")


class HintUnlockForm(FlaskForm):
    submit = SubmitField("Unlock Hint (costs points)")
