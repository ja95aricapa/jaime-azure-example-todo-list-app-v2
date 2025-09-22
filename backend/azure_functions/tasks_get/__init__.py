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
        logger.warning("Acceso no autorizado a tasks_get")
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    try:
        _, _, tasks_container = db.get_containers()
    except Exception as e:
        logger.exception("No se pudo obtener contenedor de tareas para %s", user.get("sub"))
        return func.HttpResponse(
            json.dumps({"error": "Could not connect to database"}),
            status_code=503,
            mimetype="application/json",
        )

    query = "SELECT * FROM c WHERE c.userId=@uid"
    params = [{"name": "@uid", "value": user["sub"]}]
    items = list(
        tasks_container.query_items(
            query=query,
            parameters=params,
            partition_key=user["sub"],  # 👈 mono-partición
        )
    )

    logger.debug("Se recuperaron %s tareas para %s", len(items), user.get("sub"))
    return func.HttpResponse(json.dumps(items), mimetype="application/json")
