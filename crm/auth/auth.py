import json
import jwt
from datetime import datetime, timezone
from ..models.user import User
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from typing import Optional, Tuple
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
    def hasher(password: str) -> str:
        return Authentication.ph.hash(password)

    @staticmethod
    def authenticate_user(username: str, password: str, db: Session) -> dict[str, str]:
        user = db.query(User).filter_by(username=username).first()
        if not user:
            raise ValueError("Nom d'utilisateur ou mot de passe incorrect")

        if not Authentication.verify_password(password, str(user.password_hash)):
            raise ValueError("Nom d'utilisateur ou mot de passe incorrect")

        user_id = user.id
        access_token = Authentication.generate_access_token(user_id)  # type: ignore
        refresh_token = Authentication.generate_refresh_token(user_id)  # type: ignore

        Authentication.register_tokens_jti(access_token, refresh_token)
        return {"access_token": access_token, "refresh_token": refresh_token}

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
    def refresh_access_token(refresh_token: str) -> dict[str, str]:
        # 1) Vérifier le refresh token
        payload = Authentication.verify_token(refresh_token)
        if payload.get("type") != "refresh_token":
            raise ValueError("Le token fourni n'est pas un token de rafraîchissement.")

        # 2) Révoquer l'ancien refresh JTI (anti-réutilisation)
        old_jti = payload.get("jti")
        if old_jti:
            jti_store.revoke(old_jti)  # utilise le jti_store module-level

        # 3) Générer les nouveaux tokens (rotation du refresh)
        user_id = int(payload["sub"])
        new_access_token = Authentication.generate_access_token(user_id)
        new_refresh_token = Authentication.generate_refresh_token(user_id)

        # 4) Enregistrer les nouveaux JTI dans la whitelist
        new_access_payload = jwt.decode(
            new_access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        new_refresh_payload = jwt.decode(
            new_refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )

        if j := new_access_payload.get("jti"):
            jti_store.add(j)
        if j := new_refresh_payload.get("jti"):
            jti_store.add(j)

        # 5) Sauvegarder les deux tokens localement (JSON)
        Authentication.save_tokens(new_access_token, new_refresh_token)

        # 6) Retourner le couple
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
        }

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
            print(token)
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
            print(token)
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
    def save_tokens(access_token: str, refresh_token: str) -> None:
        """Sauvegarde access+refresh dans un seul fichier JSON."""
        data = {"access_token": access_token, "refresh_token": refresh_token}
        TOKEN_PATH.write_text(json.dumps(data), encoding="utf-8")

    @staticmethod
    def load_tokens() -> Optional[Tuple[Optional[str], Optional[str]]]:
        """Charge access+refresh depuis le fichier (si JSON), sinon (legacy) retourne (token_brut, None)."""
        if not TOKEN_PATH.exists():
            return None
        raw = TOKEN_PATH.read_text(encoding="utf-8", errors="ignore").strip()
        if not raw:
            return None
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
                return obj.get("access_token"), obj.get("refresh_token")
            except json.JSONDecodeError:
                return None
        # legacy: fichier contient juste l'access token
        return raw, None

    # rétrocompatibilité (appelée un peu partout)
    @staticmethod
    def save_token(token: str) -> None:
        """DEPRECATED: sauvegarde uniquement l'access token en clair (legacy)."""
        TOKEN_PATH.write_text(token, encoding="utf-8")

    @staticmethod
    def load_token() -> Optional[str]:
        """
        Rétrocompat: si le fichier contient du JSON, on renvoie l'access_token.
        Sinon on renvoie le contenu brut (legacy).
        """
        tokens = Authentication.load_tokens()
        if tokens is None:
            return None
        access, _ = tokens
        return access

    @staticmethod
    def register_tokens_jti(
        access_token: str, refresh_token: Optional[str] = None
    ) -> None:
        store = JTIManager()
        try:
            p = Authentication.verify_token_without_jti(access_token)
            if j := p.get("jti"):
                store.add(j)
        except Exception:
            pass
        if refresh_token:
            try:
                p = Authentication.verify_token_without_jti(refresh_token)
                if j := p.get("jti"):
                    store.add(j)
            except Exception:
                pass
