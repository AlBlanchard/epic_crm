import jwt
from datetime import datetime, timezone
from crm.models import User
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from typing import Optional
from .config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRES,
    JWT_REFRESH_TOKEN_EXPIRES,
    TOKEN_PATH,
)


class Authentication:
    ph = PasswordHasher(
        time_cost=3,  # nombre d'itérations
        memory_cost=65536,  # mémoire utilisée en KB (64MB ici)
        parallelism=4,  # threads
    )

    @staticmethod
    def authenticate_user(username: str, password: str, db: Session) -> dict[str, str]:
        user = db.query(User).filter_by(username=username).first()
        if not user:
            raise ValueError("Invalid credentials")

        try:
            Authentication.verify_password(password, str(user.password_hash))
        except Exception:
            raise ValueError("Invalid credentials")

        user_id = user.id.scalar()
        department_name = user.department.name.scalar()

        return {
            "access_token": Authentication.generate_access_token(
                user_id, department_name
            ),
            "refresh_token": Authentication.generate_refresh_token(
                user_id, department_name
            ),
        }

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def verify_password(raw_password: str, hashed_password: str) -> bool:
        """Vérifie si le mot de passe brut correspond au mot de passe haché."""
        try:
            hash_value = str(hashed_password) if hashed_password is not None else ""
            return Authentication.ph.verify(hash_value, raw_password)
        except Exception:
            return False

    @staticmethod
    def save_token(token: str):
        """Enregistre le token dans un fichier local."""
        TOKEN_PATH.write_text(token)

    @staticmethod
    def load_token() -> Optional[str]:
        """Charge le token depuis le fichier local."""
        if TOKEN_PATH.exists():
            return TOKEN_PATH.read_text()
        return None
