from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, URL


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class JournalistForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=200)])
    outlet = StringField("Outlet", validators=[DataRequired(), Length(max=200)])
    beat = StringField("Beat", validators=[DataRequired(), Length(max=120)])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=2000)])
    profile_photo_url = StringField("Profile photo URL", validators=[Optional(), URL(), Length(max=500)])
    submit = SubmitField("Save")


class RatingForm(FlaskForm):
    score = IntegerField("Overall score", validators=[DataRequired(), NumberRange(min=1, max=5)])
    accuracy = IntegerField("Accuracy", validators=[DataRequired(), NumberRange(min=1, max=5)])
    sourcing = IntegerField("Sourcing", validators=[DataRequired(), NumberRange(min=1, max=5)])
    fairness = IntegerField("Fairness", validators=[DataRequired(), NumberRange(min=1, max=5)])
    transparency = IntegerField("Transparency", validators=[DataRequired(), NumberRange(min=1, max=5)])
    article_url = StringField("Article URL (optional)", validators=[Optional(), URL(), Length(max=500)])
    article_title = StringField("Article title (if linking)", validators=[Optional(), Length(max=300)])
    comment = TextAreaField("Comment", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Post rating")


class FlagForm(FlaskForm):
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Report")


class SortForm(FlaskForm):
    sort = SelectField("Sort", choices=[("newest", "Newest"), ("highest", "Highest"), ("lowest", "Lowest")])
