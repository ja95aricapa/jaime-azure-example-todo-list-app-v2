import azure.functions as func
import json, uuid
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
        _, _, tasks_container = db.get_containers()
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

    title = body.get("title")
    if not title:
        return func.HttpResponse(
            json.dumps({"error": "title is required"}),
            status_code=400,
            mimetype="application/json",
        )

    task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "status": body.get("status", "pending"),
        "userId": user["sub"],
    }

    tasks_container.create_item(task)

    return func.HttpResponse(
        json.dumps(task), status_code=201, mimetype="application/json"
    )
