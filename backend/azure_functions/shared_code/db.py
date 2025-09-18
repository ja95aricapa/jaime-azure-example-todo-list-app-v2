import os
import time
from azure.cosmos import CosmosClient, PartitionKey, exceptions

COSMOS_URI = os.getenv("COSMOS_URI", "https://127.0.0.1:8081")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_VERIFY = os.getenv("COSMOS_VERIFY", "true").lower() == "true"

DATABASE_NAME = os.getenv("COSMOS_DB_NAME", "todoapp")
USER_CONTAINER = os.getenv("COSMOS_USERS_CONTAINER", "users")
TASK_CONTAINER = os.getenv("COSMOS_TASKS_CONTAINER", "tasks")

_client = _db = _users = _tasks = None


def _connect_once():
    """
    Hace la conexión y crea DB/contenedores si no existen.
    Se llama sólo cuando aún no hay conexión (lazy init).
    """
    # Agregamos un timeout a la conexión del cliente
    client = CosmosClient(
        COSMOS_URI,
        credential=COSMOS_KEY,
        connection_verify=COSMOS_VERIFY,
        connection_timeout=30,  # Timeout de conexión de 30 segundos
    )
    db = client.create_database_if_not_exists(id=DATABASE_NAME)
    users = db.create_container_if_not_exists(
        id=USER_CONTAINER, partition_key=PartitionKey(path="/email")
    )
    tasks = db.create_container_if_not_exists(
        id=TASK_CONTAINER, partition_key=PartitionKey(path="/userId")
    )
    return client, db, users, tasks


# Aumentamos los valores por defecto para darle más tiempo al emulador
def get_containers(max_retries: int = 10, base_delay: float = 1.5):
    """
    Devuelve (db, users_container, tasks_container).
    Reintenta con backoff si Cosmos todavía está calentando (503).
    """
    global _client, _db, _users, _tasks
    if _client is not None:
        return _db, _users, _tasks

    last_err = None
    print(
        f"Attempting to connect to Cosmos DB... (retries={max_retries}, delay={base_delay}s)"
    )
    for i in range(max_retries):
        try:
            _client, _db, _users, _tasks = _connect_once()
            print("Successfully connected to Cosmos DB!")
            return _db, _users, _tasks
        except exceptions.CosmosHttpResponseError as e:
            # 503 típico mientras el emulador “arranca”
            wait_time = base_delay * (2**i)
            print(
                f"Connection failed (attempt {i+1}/{max_retries}). Retrying in {wait_time:.2f} seconds..."
            )
            last_err = e
            time.sleep(wait_time)
        except Exception as e:
            # Captura otros errores de conexión, como timeouts
            wait_time = base_delay * (2**i)
            print(
                f"An unexpected connection error occurred (attempt {i+1}/{max_retries}): {e}. Retrying in {wait_time:.2f} seconds..."
            )
            last_err = e
            time.sleep(wait_time)

    # Si no se pudo luego de reintentos, que el handler HTTP lo informe como 503.
    print("Failed to connect to Cosmos DB after all retries.")
    raise last_err
