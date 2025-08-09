import datetime

from ..database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    DateTime,
)
from functools import partial

utcnow = partial(datetime.datetime.now, datetime.timezone.utc)


class AbstractBase(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
