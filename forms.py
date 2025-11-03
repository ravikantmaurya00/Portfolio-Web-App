from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField, PasswordField, URLField
from wtforms.validators import DataRequired, Length, Email, Optional

class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField("Subject", validators=[Optional(), Length(max=255)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Send")

class ProjectForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=140)])
    short_description = StringField("Short description", validators=[DataRequired(), Length(max=255)])
    long_description = TextAreaField("Detailed description", validators=[Optional()])
    project_url = URLField("Project URL", validators=[Optional(), Length(max=255)])
    image = FileField("Project image (optional)")
    submit = SubmitField("Save")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
