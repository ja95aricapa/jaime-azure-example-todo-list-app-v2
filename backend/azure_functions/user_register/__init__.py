import azure.functions as func
import json, uuid
import bcrypt
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

    # Chequeo explícito de existencia (rápido porque /email es partition key)
    existing = list(
        users_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE c.email=@e",
            parameters=[{"name": "@e", "value": email}],
            partition_key=email,
        )
    )
    if existing and existing[0] > 0:
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
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": "Could not create user", "details": str(e)}),
            status_code=409,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps({"message": "usuario creado", "id": user["id"]}),
        status_code=201,
        mimetype="application/json",
    )
