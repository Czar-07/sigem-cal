"""
Protecao das areas administrativas do SIGEM CAL.
"""
from functools import wraps
from flask import jsonify, redirect, request, session, url_for

ADMIN_HTML_PATHS = {
    "/", "/dashboard", "/instruments", "/calibrations",
    "/reports", "/certificates", "/settings",
}

PUBLIC_GET_PREFIXES = (
    "/device/",
    "/api/public/devices/",
)

def is_admin_authenticated() -> bool:
    return bool(session.get("admin_authenticated"))

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if is_admin_authenticated():
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "message": "Autenticação administrativa necessária."
            }), 401
        return redirect(url_for("auth.admin_login", next=request.full_path))
    return wrapped

def register_auth_middleware(app):
    @app.before_request
    def protect_admin_area():
        path = request.path

        if (
            path.startswith("/static/")
            or path in {"/admin/login", "/admin/logout"}
            or (request.method == "GET" and path.startswith(PUBLIC_GET_PREFIXES))
        ):
            return None

        if path.startswith("/api/devices/") and request.method == "GET":
            return None

        if path.startswith("/api/public/devices/") and request.method == "GET":
            return None

        if path == "/api/sync/version" and request.method == "GET":
            return None

        if path in ADMIN_HTML_PATHS or path.startswith("/api/"):
            if is_admin_authenticated():
                return None
            if path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "message": "Autenticação administrativa necessária."
                }), 401
            return redirect(url_for("auth.admin_login", next=request.full_path))

        return None
