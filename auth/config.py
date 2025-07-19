import os
from datetime import timedelta


def parse_duration(value: str) -> timedelta:
    """Parse une chaîne de caractères en un objet timedelta."""
    unit = value[-1]
    number = int(value[:-1])
    if unit == "h":
        return timedelta(hours=number)
    elif unit == "d":
        return timedelta(days=number)
    elif unit == "m":
        return timedelta(minutes=number)
    else:
        raise ValueError(f"Unsupported time format: {value}")


JWT_SECRET = os.getenv("JWT_SECRET_KEY", "default_secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "algorithm")
JWT_ACCESS_TOKEN_EXPIRES = parse_duration(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "access_expire")
)
JWT_REFRESH_TOKEN_EXPIRES = parse_duration(
    os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "refresh_expire")
)
