import datetime
import json
import logging

import azure.functions as func
import bcrypt
import jwt

from shared_code import db
from shared_code.utils import get_jwt_secret

logger = logging.getLogger(__name__)


def _verify_password(plain_password: str, stored_hash: str) -> bool:
    # Compatibilidad: si lo almacenado parece bcrypt, verifica bcrypt; si no, compara texto (legacy).
    try:
        if stored_hash and stored_hash.startswith("$2"):
            return bcrypt.checkpw(plain_password.encode("utf-8"), stored_hash.encode("utf-8"))
        # Legacy fallback (no recomendado, sólo para transición)
        return plain_password == stored_hash
    except Exception:
        return False


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _, users_container, _ = db.get_containers()
    except Exception as e:
        logger.exception("No se pudo conectar a Cosmos DB durante login")
        return func.HttpResponse(
            json.dumps({"error": "Could not connect to database"}),
            status_code=503,
            mimetype="application/json",
        )

    try:
        body = req.get_json()
    except ValueError:
        logger.warning("Payload inválido en login")
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json",
        )

    email = (body.get("email") or "").strip().lower()
    password = body.get("password")

    if not email or not password:
        logger.info("Intento de login sin credenciales completas")
        return func.HttpResponse(
            json.dumps({"error": "Credenciales inválidas"}),
            status_code=401,
            mimetype="application/json",
        )

    query = "SELECT * FROM c WHERE c.email=@e"
    params = [{"name": "@e", "value": email}]
    items = list(
        users_container.query_items(
            query=query,
            parameters=params,
            partition_key=email,  # 👈 mono-partición por /email
        )
    )

    if not items or not _verify_password(password or "", items[0].get("password", "")):
        logger.info("Login fallido para %s", email)
        return func.HttpResponse(
            json.dumps({"error": "Credenciales inválidas"}),
            status_code=401,
            mimetype="application/json",
        )

    user_data = items[0]
    payload = {
        "sub": user_data["id"],
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    try:
        secret = get_jwt_secret()
    except RuntimeError as err:
        logger.error("Configuración de JWT inválida: %s", err)
        return func.HttpResponse(
            json.dumps({"error": "Authentication service misconfigured"}),
            status_code=500,
            mimetype="application/json",
        )

    token = jwt.encode(payload, secret, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    logger.info("Login exitoso para %s", email)

    return func.HttpResponse(json.dumps({"token": token}), mimetype="application/json")
