from enum import Enum


class UserRole(str, Enum):
    SALES = "sales"
    SUPPORT = "support"
    MANAGEMENT = "management"

    @classmethod
    def values(cls):
        return [role.value for role in cls]

    @classmethod
    def has_value(cls, value):
        return value in cls.values()
