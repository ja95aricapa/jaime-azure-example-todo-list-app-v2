import azure.functions as func
import json, jwt, datetime, os
from shared_code import db

SECRET = os.getenv("JWT_SECRET", "supersecret")


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

    query = "SELECT * FROM c WHERE c.email=@e"
    params = [{"name": "@e", "value": email}]
    # Note: enable_cross_partition_query is not needed if 'email' is the partition key
    items = list(
        users_container.query_items(
            query=query, parameters=params, enable_cross_partition_query=True
        )
    )

    if not items or items[0].get("password") != password:
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
    token = jwt.encode(payload, SECRET, algorithm="HS256")

    return func.HttpResponse(json.dumps({"token": token}), mimetype="application/json")
