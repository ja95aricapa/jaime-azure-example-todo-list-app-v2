import azure.functions as func
import json
from shared_code import db
from shared_code.utils import get_user_from_token


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

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json",
        )

    user_id = user["sub"]

    try:
        # Como la partición es /email, usamos el email del token
        existing = users_container.read_item(item=user_id, partition_key=user["email"])
    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "User profile not found"}),
            status_code=404,
            mimetype="application/json",
        )

    if "name" in body:
        existing["name"] = body["name"]
    if "email" in body:
        existing["email"] = body[
            "email"
        ]  # ⚠️ cambiar email implica cambiar partition key en un diseño real

    users_container.upsert_item(existing)

    # No devuelvas la contraseña en la respuesta
    if "password" in existing:
        del existing["password"]

    return func.HttpResponse(
        json.dumps({"message": "Perfil actualizado", "user": existing}),
        mimetype="application/json",
    )
