import os, jwt
from jwt import ExpiredSignatureError, InvalidTokenError

SECRET = os.getenv("JWT_SECRET", "supersecret")


def get_user_from_token(req):
    auth = req.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        # Token expirado
        return None
    except InvalidTokenError:
        # Token inválido / manipulado
        return None
    except Exception:
        return None
