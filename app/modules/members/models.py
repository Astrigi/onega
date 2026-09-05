from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


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

    # Обратная сторона связи User -> Member (протокол 002).
    # uselist=False: у одного Member максимум один связанный User.
    user: Mapped[Optional["User"]] = relationship(
        back_populates="member",
        uselist=False,
    )

    member_plots: Mapped[list["MemberPlot"]] = relationship(
        back_populates="member",
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

    # --- Голосование (протокол 004 + решение по совладению) ---
    # Правило: 1 участок = 1 голос, голосует ровно один человек.
    # - Если владелец у участка один — он автоматически представитель
    #   (выставляется в add_member_plot()).
    # - Если владельцев несколько — представителя назначает ADMIN/BOARD
    #   (set_voting_representative), либо он определяется автоматически,
    #   если все совладельцы, кроме одного, отказались от голоса
    #   (waive_voting_right).
    # На уровне БД гарантируется миграцией: не более одного
    # is_voting_representative=true на один plot_id (частичный уникальный
    # индекс), см. migrations/versions/*_add_voting_fields_to_member_plots.py
    is_voting_representative: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Совладелец добровольно отказался от права голоса по этому участку.
    voting_waived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    member: Mapped["Member"] = relationship(
        back_populates="member_plots",
    )

    plot: Mapped["Plot"] = relationship(
        back_populates="member_plots",
    )
