import os
from dotenv import load_dotenv

load_dotenv()

DATABASE = {
    "driver": "postgresql",
    "admin_user": os.getenv("ADMIN_USER"),
    "admin_password": os.getenv("ADMIN_PASSWORD"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
}


def get_database_url():
    return f"{DATABASE['driver']}://{DATABASE['user']}:{DATABASE['password']}@{DATABASE['host']}:{DATABASE['port']}/{DATABASE['database']}"


def get_admin_url():
    return f"{DATABASE['driver']}://{DATABASE['admin_user']}:{DATABASE['admin_password']}@{DATABASE['host']}:{DATABASE['port']}/postgres"
