from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_db, require_permission
from app.modules.members import service as members_service
from app.modules.plots.models import Plot, Street
from app.modules.plots.schemas import (
    PlotCreate,
    PlotOut,
    PlotUpdate,
    StreetOut,
    VotingRepresentativeRequest,
)
from app.modules.members.schemas import MemberPlotOut, VotingActionRequest
from app.modules.users.models import User


router = APIRouter(tags=["plots"])


@router.get("/streets", response_model=list[StreetOut])
def list_streets(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("plots.read")),
):
    return db.scalars(
        select(Street).order_by(Street.sort_order)
    ).all()


@router.get("/plots", response_model=list[PlotOut])
def list_plots(
    street_id: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("plots.read")),
):
    query = select(Plot).options(selectinload(Plot.member_plots))

    if street_id is not None:
        query = query.where(Plot.street_id == street_id)

    return db.scalars(query).all()


@router.post("/plots", response_model=PlotOut, status_code=201)
def create_plot(
    payload: PlotCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("plots.write")),
):
    plot = Plot(**payload.model_dump())

    db.add(plot)
    db.commit()
    db.refresh(plot)

    return plot


@router.get("/plots/{plot_id}", response_model=PlotOut)
def get_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("plots.read")),
):
    plot = db.scalar(
        select(Plot)
        .options(selectinload(Plot.member_plots))
        .where(Plot.id == plot_id)
    )

    if plot is None:
        raise HTTPException(status_code=404, detail="Участок не найден")

    return plot


@router.patch("/plots/{plot_id}", response_model=PlotOut)
def update_plot(
    plot_id: int,
    payload: PlotUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("plots.write")),
):
    plot = db.get(Plot, plot_id)

    if plot is None:
        raise HTTPException(status_code=404, detail="Участок не найден")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plot, field, value)

    db.commit()
    db.refresh(plot)

    return plot


# --- Голосование по участку (протокол 004 + правило совладения) ---


def _resolve_actor_can_act_for_member(user: User, member_id: int) -> bool:
    """
    Действие по своему голосу доступно самому совладельцу (через привязку
    User<->Member), либо ADMIN/BOARD (permission members.write).
    """
    from app.core.permissions import has_permission

    if has_permission(user, "members.write"):
        return True

    return user.member_id == member_id


@router.get("/plots/{plot_id}/voting-representative", response_model=MemberPlotOut | None)
def get_voting_representative(
    plot_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("plots.read")),
):
    return members_service.get_voting_representative(db, plot_id)


@router.post("/plots/{plot_id}/voting-representative", response_model=MemberPlotOut)
def set_voting_representative(
    plot_id: int,
    payload: VotingRepresentativeRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("members.write")),
):
    """Назначение голосующего по участку. Только ADMIN/BOARD."""
    try:
        return members_service.set_voting_representative(
            db, plot_id=plot_id, member_id=payload.member_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/plots/{plot_id}/voting-waiver", response_model=MemberPlotOut)
def waive_vote(
    plot_id: int,
    payload: VotingActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("plots.read")),
):
    """
    Отказ от права голоса по участку. Доступно самому совладельцу
    (по своей привязке User<->Member) или ADMIN/BOARD.
    """
    if not _resolve_actor_can_act_for_member(user, payload.member_id):
        raise HTTPException(
            status_code=403,
            detail="Можно отказаться только от своего собственного голоса",
        )

    try:
        return members_service.waive_voting_right(
            db, plot_id=plot_id, member_id=payload.member_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/plots/{plot_id}/voting-waiver", response_model=MemberPlotOut)
def unwaive_vote(
    plot_id: int,
    payload: VotingActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("plots.read")),
):
    """Отмена ранее сделанного отказа от голоса. Те же права, что и на отказ."""
    if not _resolve_actor_can_act_for_member(user, payload.member_id):
        raise HTTPException(
            status_code=403,
            detail="Можно отменить только свой собственный отказ",
        )

    try:
        return members_service.unwaive_voting_right(
            db, plot_id=plot_id, member_id=payload.member_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
