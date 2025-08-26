from __future__ import annotations
from enum import Enum, auto
from typing import Literal


# --- Domain enums / types ---
class Crud(Enum):
    ONLY_ADMIN = auto()
    CREATE = auto()
    READ = auto()
    READ_OWN = auto()
    UPDATE = auto()
    UPDATE_OWN = auto()
    DELETE = auto()
    DELETE_OWN = auto()


Resource = Literal["user", "client", "contract", "event"]

# --- Rôles connus ---
ROLE_ADMIN = "admin"
ROLE_MANAGEMENT = "management"
ROLE_SALES = "sales"
ROLE_SUPPORT = "support"

# --- Matrice de base par rôle ---
ROLE_RULES: dict[str, dict[str, set[Crud]]] = {
    ROLE_ADMIN: {
        "*": {Crud.CREATE, Crud.READ, Crud.UPDATE, Crud.DELETE, Crud.ONLY_ADMIN}
    },
    ROLE_MANAGEMENT: {
        "client": {Crud.READ},
        "contract": {Crud.CREATE, Crud.READ, Crud.UPDATE},
        "event": {Crud.READ, Crud.UPDATE},
        "user": {Crud.CREATE, Crud.READ, Crud.UPDATE, Crud.DELETE, Crud.UPDATE_OWN},
        # Attention ici il s'agit de la classe UserRole qui fait le lien entre User et Role
        # Les managers ont le droit d'associer des rôles aux utilisateurs (et de les enlever)
        "user_role": {Crud.CREATE, Crud.DELETE},
    },
    ROLE_SALES: {
        "client": {Crud.CREATE, Crud.READ, Crud.UPDATE_OWN},
        "contract": {Crud.READ, Crud.UPDATE_OWN},
        "event": {Crud.READ, Crud.CREATE},
        "user": {Crud.READ_OWN, Crud.UPDATE_OWN},
    },
    ROLE_SUPPORT: {
        "client": {Crud.READ},
        "contract": {Crud.READ},
        "event": {Crud.READ, Crud.UPDATE_OWN},
        "user": {Crud.READ_OWN, Crud.UPDATE_OWN},
    },
}
