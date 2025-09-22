import logging
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
logger = logging.getLogger(__name__)


def _connect_once():
    """
    Hace la conexión y crea DB/contenedores si no existen.
    Se llama sólo cuando aún no hay conexión (lazy init).
    """
    client = CosmosClient(
        COSMOS_URI,
        credential=COSMOS_KEY,
        connection_verify=COSMOS_VERIFY,
        connection_timeout=30,  # Timeout de conexión de 30 segundos
    )
    db = client.create_database_if_not_exists(id=DATABASE_NAME)

    # Unique Key Policy para asegurar unicidad de /email
    unique_key_policy = {"uniqueKeys": [{"paths": ["/email"]}]}

    users = db.create_container_if_not_exists(
        id=USER_CONTAINER,
        partition_key=PartitionKey(path="/email"),
        unique_key_policy=unique_key_policy,
    )

    tasks = db.create_container_if_not_exists(
        id=TASK_CONTAINER, partition_key=PartitionKey(path="/userId")
    )
    return client, db, users, tasks


def get_containers(max_retries: int = 10, base_delay: float = 1.5):
    """
    Devuelve (db, users_container, tasks_container).
    Reintenta con backoff si Cosmos todavía está calentando (503).
    """
    global _client, _db, _users, _tasks
    if _client is not None:
        return _db, _users, _tasks

    last_err = None
    logger.info(
        "Intentando conectar a Cosmos DB (retries=%s, delay=%ss)",
        max_retries,
        base_delay,
    )
    for i in range(max_retries):
        try:
            _client, _db, _users, _tasks = _connect_once()
            logger.info("Conectado a Cosmos DB correctamente")
            return _db, _users, _tasks
        except exceptions.CosmosHttpResponseError as e:
            wait_time = base_delay * (2**i)
            logger.warning(
                "Fallo al conectar a Cosmos DB (intento %s/%s). Reintentando en %.2f s. Detalle: %s",
                i + 1,
                max_retries,
                wait_time,
                e,
                exc_info=True,
            )
            last_err = e
            time.sleep(wait_time)
        except Exception as e:
            wait_time = base_delay * (2**i)
            logger.exception(
                "Error inesperado al conectar a Cosmos DB (intento %s/%s)",
                i + 1,
                max_retries,
            )
            last_err = e
            time.sleep(wait_time)

    logger.error("No fue posible conectar a Cosmos DB tras todos los reintentos")
    raise last_err
