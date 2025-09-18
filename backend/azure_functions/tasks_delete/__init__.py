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
        tasks_container.delete_item(item=task_id, partition_key=user["sub"])
    except Exception as e:
        return func.HttpResponse(
            json.dumps(
                {"error": "Task not found or could not be deleted", "details": str(e)}
            ),
            status_code=404,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps({"message": "deleted"}), mimetype="application/json"
    )
