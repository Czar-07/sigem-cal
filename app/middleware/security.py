"""Cabeçalhos e políticas HTTP de segurança."""

from flask import request


def register_security_headers(app):
    @app.after_request
    def security_headers(response):
        # ============================================================
        # HEADERS DE SEGURANÇA
        # ============================================================

        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )

        response.headers.setdefault(
            "X-Frame-Options",
            "SAMEORIGIN",
        )

        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )

        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )

        # ============================================================
        # CONTENT SECURITY POLICY
        # ============================================================

        response.headers.setdefault(
            "Content-Security-Policy",
            (
                "default-src 'self'; "

                # Imagens
                "img-src 'self' data: blob: https:; "

                # CSS
                "style-src 'self' 'unsafe-inline' "
                "https://cdn.jsdelivr.net "
                "https://fonts.googleapis.com "
                "https://cdn.datatables.net; "

                # JavaScript
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.jsdelivr.net "
                "https://code.jquery.com "
                "https://cdn.datatables.net; "

                # Fontes
                "font-src 'self' data: "
                "https://cdn.jsdelivr.net "
                "https://fonts.gstatic.com; "

                # APIs / AJAX / Fetch
                "connect-src 'self' https:; "

                # Objetos/plugins antigos
                "object-src 'none'; "

                # Base URL
                "base-uri 'self'; "

                # Frames
                "frame-ancestors 'self';"
            ),
        )

        # ============================================================
        # HSTS
        # ============================================================

        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response