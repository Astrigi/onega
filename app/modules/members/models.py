from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)

    surname: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    patronymic: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MemberPlot(Base):
    __tablename__ = "member_plots"

    id: Mapped[int] = mapped_column(primary_key=True)

    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
    )

    plot_id: Mapped[int] = mapped_column(
        ForeignKey("plots.id", ondelete="RESTRICT"),
        nullable=False,
    )

    ownership_share: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    member: Mapped["Member"] = relationship()

    plot: Mapped["Plot"] = relationship()
