import jwt
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timezone
from auth.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRES,
    JWT_REFRESH_TOKEN_EXPIRES,
)


def generate_access_token(user_id: int, department_name: str) -> str:
    """Génère un token d'accès JWT pour l'utilisateur."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "department": department_name,
        "iat": now,
        "exp": now + JWT_ACCESS_TOKEN_EXPIRES,
        "type": "access_token",
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def generate_refresh_token(user_id: int, department_name: str) -> str:
    """Génère un token de rafraîchissement JWT pour l'utilisateur."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "department": department_name,
        "iat": now,
        "exp": now + JWT_REFRESH_TOKEN_EXPIRES,
        "type": "refresh_token",
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> dict:
    """Vérifie un token JWT et retourne le payload."""
    try:
        payload = decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except InvalidTokenError:
        raise ValueError("Invalid token")
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")
