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
        _, _, tasks_container = db.get_containers()
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": "Could not connect to database", "details": str(e)}),
            status_code=503,
            mimetype="application/json",
        )

    task_id = req.route_params.get("id")
    if not task_id:
        return func.HttpResponse(
            json.dumps({"error": "Task ID is required"}),
            status_code=400,
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

    try:
        task = tasks_container.read_item(item=task_id, partition_key=user["sub"])
    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "Task not found"}),
            status_code=404,
            mimetype="application/json",
        )

    allowed_fields = {"title", "status"}
    update_data = {k: v for k, v in body.items() if k in allowed_fields}

    allowed_statuses = {"pending", "in_progress", "done", "blocked"}
    if "status" in update_data and update_data["status"] not in allowed_statuses:
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "Invalid status",
                    "allowed": sorted(list(allowed_statuses)),
                }
            ),
            status_code=400,
            mimetype="application/json",
        )

    # Aplica cambios permitidos
    for k, v in update_data.items():
        task[k] = v

    # Explicitamente NO permitir cambiar id / userId
    task["id"] = task_id
    task["userId"] = user["sub"]

    tasks_container.upsert_item(task)

    return func.HttpResponse(json.dumps(task), mimetype="application/json")
