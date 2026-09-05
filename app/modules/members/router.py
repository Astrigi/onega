from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_db, require_permission
from app.modules.members import service
from app.modules.members.models import Member
from app.modules.members.schemas import (
    AddMemberPlotRequest,
    LinkUserRequest,
    MemberCreate,
    MemberOut,
    MemberUpdate,
)
from app.modules.users.models import User


router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=list[MemberOut])
def list_members(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("members.read")),
):
    members = db.scalars(
        select(Member).options(selectinload(Member.member_plots))
    ).all()

    return members


@router.post("", response_model=MemberOut, status_code=201)
def create_member(
    payload: MemberCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("members.write")),
):
    member = Member(**payload.model_dump())

    db.add(member)
    db.commit()
    db.refresh(member)

    return member


@router.get("/{member_id}", response_model=MemberOut)
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("members.read")),
):
    member = db.scalar(
        select(Member)
        .options(selectinload(Member.member_plots))
        .where(Member.id == member_id)
    )

    if member is None:
        raise HTTPException(status_code=404, detail="Член СНТ не найден")

    return member


@router.patch("/{member_id}", response_model=MemberOut)
def update_member(
    member_id: int,
    payload: MemberUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("members.write")),
):
    member = db.get(Member, member_id)

    if member is None:
        raise HTTPException(status_code=404, detail="Член СНТ не найден")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)

    return member


@router.post("/{member_id}/plots", response_model=MemberOut, status_code=201)
def add_member_plot(
    member_id: int,
    payload: AddMemberPlotRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("members.write")),
):
    member = db.get(Member, member_id)

    if member is None:
        raise HTTPException(status_code=404, detail="Член СНТ не найден")

    try:
        service.add_member_plot(
            db,
            member_id=member_id,
            plot_id=payload.plot_id,
            ownership_share=payload.ownership_share,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.refresh(member)
    return member


@router.post("/{member_id}/link-user", response_model=MemberOut)
def link_user(
    member_id: int,
    payload: LinkUserRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("members.write")),
):
    """
    Привязка пользователя системы к записи собственника (протокол 002).
    Доступно только ADMIN/BOARD (permission members.write).
    """
    member = db.get(Member, member_id)

    if member is None:
        raise HTTPException(status_code=404, detail="Член СНТ не найден")

    target_user = db.get(User, payload.user_id)

    if target_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if target_user.member_id is not None and target_user.member_id != member_id:
        raise HTTPException(
            status_code=409,
            detail="Этот пользователь уже привязан к другому члену СНТ",
        )

    existing = db.scalar(
        select(User).where(User.member_id == member_id, User.id != target_user.id)
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Этот член СНТ уже привязан к другому пользователю",
        )

    target_user.member_id = member_id

    db.commit()
    db.refresh(member)

    return member


@router.delete("/{member_id}/link-user", response_model=MemberOut)
def unlink_user(
    member_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("members.write")),
):
    member = db.get(Member, member_id)

    if member is None:
        raise HTTPException(status_code=404, detail="Член СНТ не найден")

    target_user = db.scalar(select(User).where(User.member_id == member_id))

    if target_user is not None:
        target_user.member_id = None
        db.commit()

    db.refresh(member)
    return member
