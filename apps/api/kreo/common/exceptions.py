"""
Erreurs au format RFC 9457 (application/problem+json).

Toute exception DRF est convertie en {type, title, status, detail, errors?, instance}.
Une transition de statut interdite renvoie 409 Conflict.
"""

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import set_rollback

PROBLEM_TYPE_BASE = "https://kreo.be/problems/"

TITLES = {
    400: "Requête invalide",
    401: "Authentification requise",
    403: "Action non autorisée",
    404: "Ressource introuvable",
    405: "Méthode non autorisée",
    409: "Conflit",
    413: "Fichier trop volumineux",
    415: "Type de fichier non pris en charge",
    422: "Données invalides",
    429: "Trop de requêtes",
    500: "Erreur interne",
}


class ProblemException(exceptions.APIException):
    """Exception de base avec un type de problème stable, exploitable par les clients."""

    status_code = status.HTTP_400_BAD_REQUEST
    problem_type = "invalid-request"
    default_detail = "La requête est invalide."
    default_code = "invalid"

    def __init__(self, detail=None, *, problem_type=None, extra=None):
        super().__init__(detail)
        if problem_type:
            self.problem_type = problem_type
        self.extra = extra or {}


class TransitionError(ProblemException):
    status_code = status.HTTP_409_CONFLICT
    problem_type = "invalid-transition"
    default_detail = "Cette transition de statut n'est pas autorisée."
    default_code = "invalid_transition"


class ConflictError(ProblemException):
    status_code = status.HTTP_409_CONFLICT
    problem_type = "conflict"
    default_detail = "Cette action entre en conflit avec l'état actuel."
    default_code = "conflict"


class BusinessRuleError(ProblemException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    problem_type = "business-rule"
    default_detail = "Cette action n'est pas permise par les règles de KREO."
    default_code = "business_rule"


class QuotaExceededError(ProblemException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    problem_type = "quota-exceeded"
    default_detail = "Tu as atteint la limite autorisée pour aujourd'hui."
    default_code = "quota_exceeded"


def _flatten_errors(detail):
    """Transforme les erreurs de validation DRF en liste {field, message, code}."""
    errors = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else str(key))
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, dict | list):
                    walk(item, path)
                else:
                    errors.append(
                        {
                            "field": path or None,
                            "message": str(item),
                            "code": getattr(item, "code", "invalid"),
                        }
                    )
        else:
            errors.append(
                {
                    "field": path or None,
                    "message": str(node),
                    "code": getattr(node, "code", "invalid"),
                }
            )

    walk(detail, "")
    return errors


def problem_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(
            detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        )

    if not isinstance(exc, exceptions.APIException):
        return None

    set_rollback()
    status_code = exc.status_code
    request = context.get("request")

    if isinstance(exc, ProblemException):
        problem_type = exc.problem_type
        detail = str(exc.detail) if not isinstance(exc.detail, dict | list) else None
        extra = exc.extra
    elif isinstance(exc, exceptions.ValidationError):
        problem_type = "validation-error"
        detail = "Certains champs sont invalides."
        extra = {}
    elif isinstance(exc, exceptions.Throttled):
        problem_type = "rate-limited"
        detail = "Trop de requêtes. Réessaie dans un instant."
        extra = {"retry_after": exc.wait}
    else:
        problem_type = exc.default_code.replace("_", "-") if exc.default_code else "error"
        detail = str(exc.detail) if not isinstance(exc.detail, dict | list) else None
        extra = {}

    body = {
        "type": PROBLEM_TYPE_BASE + problem_type,
        "title": TITLES.get(status_code, "Erreur"),
        "status": status_code,
    }
    if detail:
        body["detail"] = detail
    if request is not None:
        body["instance"] = request.get_full_path()
    if isinstance(exc.detail, dict | list):
        body["errors"] = _flatten_errors(exc.detail)
    body.update(extra)

    headers = {}
    if getattr(exc, "auth_header", None):
        headers["WWW-Authenticate"] = exc.auth_header
    if getattr(exc, "wait", None):
        headers["Retry-After"] = str(int(exc.wait))

    response = Response(body, status=status_code, headers=headers)
    response.content_type = "application/problem+json"
    return response
