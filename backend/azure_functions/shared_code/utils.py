import logging
import os
from functools import lru_cache

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger(__name__)


@lru_cache()
def get_jwt_secret() -> str:
    """Obtiene el secreto JWT desde variables de entorno.

    Se cachea para evitar lecturas repetidas. En caso de no estar configurado
    se lanza una excepción para que el servicio falle de forma explícita.
    """

    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        logger.error("JWT_SECRET no está configurado")
        raise RuntimeError("JWT_SECRET environment variable is required")
    return secret


def get_user_from_token(req):
    auth = req.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        logger.debug("Solicitud sin token Bearer")
        return None

    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        return payload
    except RuntimeError:
        # get_jwt_secret ya dejó registro; propagamos para que el caller trate el error como 500
        raise
    except ExpiredSignatureError:
        logger.info("Token expirado")
        return None
    except InvalidTokenError:
        logger.warning("Token inválido")
        return None
    except Exception as exc:
        logger.exception("Error inesperado al decodificar token: %s", exc)
        return None
