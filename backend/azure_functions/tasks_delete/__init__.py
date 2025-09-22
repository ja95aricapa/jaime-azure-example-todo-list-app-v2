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
        logger.warning("Acceso no autorizado a eliminar tarea")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    try:
        _, _, tasks_container = db.get_containers()
    except Exception as e:
        logger.exception("No se pudo conectar a Cosmos DB al eliminar tarea")
        return func.HttpResponse(
            json.dumps({"error": "Could not connect to database"}),
            status_code=503,
            mimetype="application/json",
        )

    task_id = req.route_params.get("id")
    if not task_id:
        logger.info("Solicitud de eliminación sin taskId")
        return func.HttpResponse(
            json.dumps({"error": "Task ID is required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        tasks_container.delete_item(item=task_id, partition_key=user["sub"])
        logger.info("Tarea %s eliminada para usuario %s", task_id, user["sub"])
    except Exception:
        logger.warning(
            "No se pudo eliminar la tarea %s para usuario %s", task_id, user["sub"],
            exc_info=True,
        )
        return func.HttpResponse(
            json.dumps({"error": "Task not found or could not be deleted"}),
            status_code=404,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps({"message": "deleted"}), mimetype="application/json"
    )
