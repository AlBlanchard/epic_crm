from crm.models import User
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from auth.token import generate_access_token, generate_refresh_token

ph = PasswordHasher(
    time_cost=3,  # nombre d'itérations
    memory_cost=65536,  # mémoire utilisée en KB (64MB ici)
    parallelism=4,  # threads
)


def authenticate_user(username: str, password: str, db: Session) -> str:
    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise ValueError("Invalid credentials")

    try:
        ph.verify(str(user.password_hash), password)
    except Exception:
        raise ValueError("Invalid credentials")

    user_id = user.id.scalar()
    department_name = user.department.name.scalar()

    return generate_access_token(user_id, department_name)
