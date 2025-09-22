import json
import logging

import azure.functions as func

from shared_code import db
from shared_code.utils import get_user_from_token

logger = logging.getLogger(__name__)


def _sanitize_user(u: dict) -> dict:
    u2 = dict(u)
    if "password" in u2:
        del u2["password"]
    return u2


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        user = get_user_from_token(req)
    except RuntimeError as err:
        logger.error("Error de configuración JWT: %s", err)
        return func.HttpResponse(
            json.dumps({"error": "Authentication service misconfigured"}),
            status_code=500,
            mimetype="application/json",
        )

    if not user:
        logger.warning("Acceso no autorizado a perfil")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    try:
        _, users_container, _ = db.get_containers()
    except Exception as e:
        logger.exception("No se pudo conectar a Cosmos DB al manejar perfil")
        return func.HttpResponse(
            json.dumps({"error": "Could not connect to database"}),
            status_code=503,
            mimetype="application/json",
        )

    user_id = user["sub"]

    # Lee el perfil actual
    try:
        existing = users_container.read_item(item=user_id, partition_key=user["email"])
    except Exception:
        logger.warning("Perfil no encontrado para %s", user_id, exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": "User profile not found"}),
            status_code=404,
            mimetype="application/json",
        )

    if req.method == "GET":
        logger.debug("Perfil consultado para %s", user_id)
        return func.HttpResponse(
            json.dumps({"user": _sanitize_user(existing)}),
            mimetype="application/json",
        )

    # PUT (update)
    try:
        body = req.get_json()
    except ValueError:
        logger.warning("JSON inválido al actualizar perfil %s", user_id)
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json",
        )

    # No permitir cambiar email (partition key)
    if "email" in body and body["email"] != existing.get("email"):
        logger.info("Intento de cambio de email para %s bloqueado", user_id)
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "Cambio de email no permitido. Contacta soporte para migración o usa un flujo dedicado."
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    if "name" in body:
        new_name = (body["name"] or "").strip()
        if not new_name:
            return func.HttpResponse(
                json.dumps({"error": "name cannot be empty"}),
                status_code=400,
                mimetype="application/json",
            )
        existing["name"] = new_name

    try:
        users_container.upsert_item(existing)
        logger.info("Perfil actualizado para %s", user_id)
    except Exception:
        logger.exception("Error al actualizar perfil %s", user_id)
        return func.HttpResponse(
            json.dumps({"error": "Could not update profile"}),
            status_code=500,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps({"message": "Perfil actualizado", "user": _sanitize_user(existing)}),
        mimetype="application/json",
    )
