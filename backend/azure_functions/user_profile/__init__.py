import azure.functions as func
import json
from shared_code import db
from shared_code.utils import get_user_from_token


def _sanitize_user(u: dict) -> dict:
    u2 = dict(u)
    if "password" in u2:
        del u2["password"]
    return u2


def main(req: func.HttpRequest) -> func.HttpResponse:
    user = get_user_from_token(req)
    if not user:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )

    try:
        _, users_container, _ = db.get_containers()
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": "Could not connect to database", "details": str(e)}),
            status_code=503,
            mimetype="application/json",
        )

    user_id = user["sub"]

    # Lee el perfil actual
    try:
        existing = users_container.read_item(item=user_id, partition_key=user["email"])
    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "User profile not found"}),
            status_code=404,
            mimetype="application/json",
        )

    if req.method == "GET":
        return func.HttpResponse(
            json.dumps({"user": _sanitize_user(existing)}),
            mimetype="application/json",
        )

    # PUT (update)
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json",
        )

    # No permitir cambiar email (partition key)
    if "email" in body and body["email"] != existing.get("email"):
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
        existing["name"] = body["name"]

    users_container.upsert_item(existing)

    return func.HttpResponse(
        json.dumps({"message": "Perfil actualizado", "user": _sanitize_user(existing)}),
        mimetype="application/json",
    )
