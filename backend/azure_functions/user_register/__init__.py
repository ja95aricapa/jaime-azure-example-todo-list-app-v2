import json
import logging
import uuid

import azure.functions as func
import bcrypt

from shared_code import db

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _, users_container, _ = db.get_containers()
    except Exception as e:
        logger.exception("No se pudo conectar a Cosmos DB durante registro")
        return func.HttpResponse(
            json.dumps({"error": "Could not connect to database"}),
            status_code=503,
            mimetype="application/json",
        )

    try:
        body = req.get_json()
    except ValueError:
        logger.warning("Payload inválido en registro")
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json",
        )

    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    name = (body.get("name") or "").strip()

    if not email or not password:
        logger.info("Intento de registro incompleto (email=%s)", email)
        return func.HttpResponse(
            json.dumps({"error": "email y password requeridos"}),
            status_code=400,
            mimetype="application/json",
        )

    if len(password) < 8:
        logger.info("Password demasiado corta para %s", email)
        return func.HttpResponse(
            json.dumps({"error": "La contraseña debe tener al menos 8 caracteres"}),
            status_code=400,
            mimetype="application/json",
        )

    # Chequeo explícito de existencia (rápido porque /email es partition key)
    existing = list(
        users_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE c.email=@e",
            parameters=[{"name": "@e", "value": email}],
            partition_key=email,
        )
    )
    if existing and existing[0] > 0:
        logger.info("Intento de registro con email duplicado: %s", email)
        return func.HttpResponse(
            json.dumps({"error": "El email ya existe"}),
            status_code=409,
            mimetype="application/json",
        )

    # Hasheo seguro
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password": hashed,  # almacenado como hash bcrypt
        "name": name,
    }

    try:
        users_container.create_item(user)
        logger.info("Usuario creado correctamente: %s", email)
    except Exception as e:
        logger.exception("Error al crear usuario %s", email)
        return func.HttpResponse(
            json.dumps({"error": "Could not create user"}),
            status_code=409,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps({"message": "usuario creado", "id": user["id"]}),
        status_code=201,
        mimetype="application/json",
    )
