from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ratemynews.extensions import db
from ratemynews.forms import LoginForm, RegisterForm
from ratemynews.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter((User.email == form.email.data) | (User.username == form.username.data)).first():
            flash("Username or email already exists.", "danger")
            return render_template("auth/register.html", form=form)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user or not user.check_password(form.password.data):
            flash("Invalid credentials.", "danger")
            return render_template("auth/login.html", form=form)
        login_user(user)
        flash("Welcome back!", "success")
        return redirect(url_for("main.home"))
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html", ratings=current_user.ratings)
