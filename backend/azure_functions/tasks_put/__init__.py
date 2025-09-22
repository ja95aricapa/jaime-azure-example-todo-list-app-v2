import json
import logging

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
        logger.warning("Intento no autorizado de actualización de tarea")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    try:
        _, _, tasks_container = db.get_containers()
    except Exception as e:
        logger.exception("No se pudo conectar a Cosmos DB al actualizar tarea")
        return func.HttpResponse(
            json.dumps({"error": "Could not connect to database"}),
            status_code=503,
            mimetype="application/json",
        )

    task_id = req.route_params.get("id")
    if not task_id:
        logger.info("Solicitud de actualización sin taskId")
        return func.HttpResponse(
            json.dumps({"error": "Task ID is required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        body = req.get_json()
    except ValueError:
        logger.warning("JSON inválido al actualizar tarea %s", task_id)
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        task = tasks_container.read_item(item=task_id, partition_key=user["sub"])
    except Exception:
        logger.warning("Tarea no encontrada %s para usuario %s", task_id, user["sub"])
        return func.HttpResponse(
            json.dumps({"error": "Task not found"}),
            status_code=404,
            mimetype="application/json",
        )

    allowed_fields = {"title", "status"}
    update_data = {}
    for key, value in body.items():
        if key not in allowed_fields:
            continue
        if key == "title":
            value = (value or "").strip()
            if not value:
                logger.info("Intento de actualizar tarea %s con título vacío", task_id)
                return func.HttpResponse(
                    json.dumps({"error": "title cannot be empty"}),
                    status_code=400,
                    mimetype="application/json",
                )
        update_data[key] = value

    allowed_statuses = {"pending", "in_progress", "done", "blocked"}
    if "status" in update_data and update_data["status"] not in allowed_statuses:
        logger.info(
            "Estado inválido %s para tarea %s", update_data["status"], task_id
        )
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "Invalid status",
                    "allowed": sorted(list(allowed_statuses)),
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    # Aplica cambios permitidos
    for k, v in update_data.items():
        task[k] = v

    # Explicitamente NO permitir cambiar id / userId
    task["id"] = task_id
    task["userId"] = user["sub"]

    try:
        tasks_container.upsert_item(task)
        logger.info("Tarea %s actualizada para usuario %s", task_id, user["sub"])
    except Exception:
        logger.exception("Error al actualizar tarea %s", task_id)
        return func.HttpResponse(
            json.dumps({"error": "Could not update task"}),
            status_code=500,
            mimetype="application/json",
        )

    return func.HttpResponse(json.dumps(task), mimetype="application/json")
