import azure.functions as func
import json, uuid
from shared_code import db


def main(req: func.HttpRequest) -> func.HttpResponse:
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

    email = body.get("email")
    password = body.get("password")
    name = body.get("name")

    if not email or not password:
        return func.HttpResponse(
            json.dumps({"error": "email y password requeridos"}),
            status_code=400,
            mimetype="application/json",
        )

    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password": password,  # ⚠️ usa bcrypt en prod
        "name": name,
    }

    try:
        users_container.create_item(user)
    except Exception as e:
        # Esto podría fallar si el email (partition key) ya existe, por ejemplo.
        return func.HttpResponse(
            json.dumps({"error": "Could not create user", "details": str(e)}),
            status_code=409,  # 409 Conflict es un buen código para 'recurso ya existe'
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps({"message": "usuario creado", "id": user["id"]}),
        status_code=201,
        mimetype="application/json",
    )
