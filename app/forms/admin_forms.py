"""
app/forms/admin_forms.py — Admin challenge create/edit form.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, SelectField, IntegerField,
    BooleanField, SubmitField, FieldList, FormField
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


CATEGORY_CHOICES = [
    ("web", "🌐 Web Exploitation"),
    ("crypto", "🔐 Cryptography"),
    ("forensics", "🔍 Forensics"),
    ("reverse", "⚙️ Reverse Engineering"),
    ("pwn", "💣 Binary Exploitation"),
    ("misc", "🎲 Miscellaneous"),
    ("network", "📡 Network"),
]

DIFFICULTY_CHOICES = [
    ("easy", "Easy"),
    ("medium", "Medium"),
    ("hard", "Hard"),
    ("insane", "Insane"),
]


class HintSubForm(FlaskForm):
    """Sub-form for inline hint fields."""
    class Meta:
        csrf = False  # CSRF handled by parent form

    text = TextAreaField("Hint Text", validators=[Optional(), Length(max=2000)])
    penalty_points = IntegerField("Penalty Points", default=25, validators=[Optional()])


class ChallengeForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description (Markdown)", validators=[DataRequired()])
    category = SelectField("Category", choices=CATEGORY_CHOICES, validators=[DataRequired()])
    difficulty = SelectField("Difficulty", choices=DIFFICULTY_CHOICES, validators=[DataRequired()])
    points = IntegerField(
        "Points", default=100, validators=[DataRequired(), NumberRange(min=10, max=1000)]
    )
    flag = StringField(
        "Flag (raw — will be SHA-256 hashed on save)",
        validators=[DataRequired(), Length(max=512)],
    )
    active = BooleanField("Active (visible to players)", default=True)
    challenge_file = FileField(
        "Challenge File (optional)",
        validators=[
            FileAllowed(
                ["zip", "txt", "png", "jpg", "pdf", "bin", "tar", "gz", "pcap"],
                "Allowed: zip, txt, png, jpg, pdf, bin, tar, gz, pcap",
            )
        ],
    )
    # One optional hint
    hint_text = TextAreaField("Hint Text (optional, Markdown)", validators=[Optional()])
    hint_penalty = IntegerField("Hint Penalty Points", default=25, validators=[Optional()])

    submit = SubmitField("Save Challenge")
