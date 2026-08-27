"""
Rotas de autenticacao administrativa.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from app.auth.services import validar_admin

auth = Blueprint("auth", __name__)

@auth.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_authenticated"):
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if validar_admin(username, password):
            session.clear()
            session["admin_authenticated"] = True
            session["admin_username"] = username.strip()
            session.permanent = True
            next_url = request.args.get("next") or request.form.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("home"))
        flash("Usuário ou senha inválidos.", "danger")
    return render_template("auth/login.html")

@auth.route("/admin/logout", methods=["GET", "POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("auth.admin_login"))
