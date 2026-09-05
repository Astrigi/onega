from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.members.models import MemberPlot


class Street(Base):
    __tablename__ = "streets"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    plots: Mapped[list["Plot"]] = relationship(
        back_populates="street",
    )


class Plot(Base):
    __tablename__ = "plots"

    __table_args__ = (
        UniqueConstraint(
            "plot_number",
            name="uq_plots_plot_number",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    street_id: Mapped[int] = mapped_column(
        ForeignKey("streets.id", ondelete="RESTRICT"),
        nullable=False,
    )

    plot_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    street: Mapped["Street"] = relationship(
        back_populates="plots",
    )

    member_plots: Mapped[list["MemberPlot"]] = relationship(
        back_populates="plot",
    )
