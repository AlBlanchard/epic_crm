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
from uuid import uuid4

from .jti_manager import JTIManager

jti_store = JTIManager()


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

        user_id = user.id

        # L'IDE détecte une erreur pour le user_id car j'utilise l'ancien typage SQLAlchemy
        # mais c'est correct car user_id est un entier
        return {
            "access_token": Authentication.generate_access_token(
                user_id  # type: ignore
            ),
            "refresh_token": Authentication.generate_refresh_token(
                user_id  # type: ignore
            ),
        }

    @staticmethod
    def generate_access_token(user_id: int) -> str:
        """Génère un token d'accès JWT pour l'utilisateur."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + JWT_ACCESS_TOKEN_EXPIRES,
            "type": "access_token",
            # jti sert à identifier le token de manière unique (sécurité ++)
            "jti": str(uuid4()),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token

    @staticmethod
    def generate_refresh_token(user_id: int) -> str:
        """Génère un token de rafraîchissement JWT pour l'utilisateur."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + JWT_REFRESH_TOKEN_EXPIRES,
            "type": "refresh_token",
            "jti": str(uuid4()),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        Rafraîchit le token d'accès en utilisant un token de rafraîchissement valide.
        """
        payload = Authentication.verify_token(refresh_token)
        if payload.get("type") != "refresh_token":
            raise ValueError("Le token fourni n'est pas un token de rafraîchissement.")

        user_id = payload["sub"]

        # Révoque l'ancien refresh token
        jti_store = JTIManager()
        old_jti = payload.get("jti")
        if old_jti:
            jti_store.revoke(old_jti)

        # Génère les nouveaux tokens
        new_access_token = Authentication.generate_access_token(user_id)
        new_refresh_token = Authentication.generate_refresh_token(user_id)

        # Enregistre les nouveaux jti
        new_access_payload = jwt.decode(
            new_access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        new_refresh_payload = jwt.decode(
            new_refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )

        jti_store.add(new_access_payload["jti"])
        jti_store.add(new_refresh_payload["jti"])

        Authentication.save_token(new_access_token)

        return new_access_token

    @staticmethod
    def verify_token(token: str) -> dict:
        """Vérifie un token JWT et retourne le payload."""
        try:
            payload = decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")
            if not jti or not jti_store.is_valid(jti):
                raise ValueError("Token has been revoked")

            return payload

        except ExpiredSignatureError:
            raise ValueError("Token has expired")
        except InvalidTokenError:
            raise ValueError("Invalid token")
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")

    @staticmethod
    def verify_token_without_jti(token: str) -> dict:
        """Vérifie un token JWT sans vérifier le jti."""
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

    @staticmethod
    def is_token_expired(token: str) -> bool:
        try:
            payload = decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": True},
            )
            return False
        except ExpiredSignatureError:
            return True
