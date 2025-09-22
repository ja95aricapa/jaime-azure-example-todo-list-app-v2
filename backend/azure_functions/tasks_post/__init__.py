import json
import logging
import uuid

import azure.functions as func

from shared_code import db
from shared_code.utils import get_user_from_token

logger = logging.getLogger(__name__)


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
        logger.warning("Intento no autorizado de creación de tarea")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    try:
        _, _, tasks_container = db.get_containers()
    except Exception as e:
        logger.exception("No se pudo conectar a Cosmos DB al crear tarea")
        return func.HttpResponse(
            json.dumps({"error": "Could not connect to database"}),
            status_code=503,
            mimetype="application/json",
        )

    try:
        body = req.get_json()
    except ValueError:
        logger.warning("JSON inválido al crear tarea")
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json",
        )

    title = (body.get("title") or "").strip()
    if not title:
        logger.info("Intento de crear tarea sin título")
        return func.HttpResponse(
            json.dumps({"error": "title is required"}),
            status_code=400,
            mimetype="application/json",
        )

    allowed_statuses = {"pending", "in_progress"}
    status = body.get("status", "pending")
    if status not in allowed_statuses:
        logger.info("Estado inválido para nueva tarea: %s", status)
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "Invalid status for new task",
                    "allowed": sorted(list(allowed_statuses)),
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "status": status,
        "userId": user["sub"],
    }

    try:
        tasks_container.create_item(task)
        logger.info("Tarea %s creada para usuario %s", task["id"], user["sub"])
    except Exception:
        logger.exception("Error al crear la tarea para %s", user["sub"])
        return func.HttpResponse(
            json.dumps({"error": "Could not create task"}),
            status_code=500,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps(task), status_code=201, mimetype="application/json"
    )
