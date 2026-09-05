from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.members.models import MemberPlot


def add_member_plot(
    db: Session,
    member_id: int,
    plot_id: int,
    ownership_share: float,
) -> MemberPlot:
    existing_rows = db.scalars(
        select(MemberPlot).where(MemberPlot.plot_id == plot_id)
    ).all()

    current_share = sum(float(row.ownership_share) for row in existing_rows)
    new_total = current_share + ownership_share

    if new_total > 100:
        raise ValueError(
            f"Сумма долей участка не может превышать 100%. "
            f"Сейчас: {current_share}%, "
            f"добавляется: {ownership_share}%"
        )

    # Голосование (протокол 004 + решение по совладению участком):
    # если это первый (и пока единственный) собственник участка —
    # он автоматически становится представителем для голосования.
    # Если совладельцев уже несколько, представителя нужно назначить
    # явно через set_voting_representative() (ADMIN/BOARD) — оставляем
    # is_voting_representative=False, чтобы не выбирать голосующего
    # неявно за правление.
    is_first_owner = len(existing_rows) == 0

    member_plot = MemberPlot(
        member_id=member_id,
        plot_id=plot_id,
        ownership_share=ownership_share,
        is_voting_representative=is_first_owner,
    )

    db.add(member_plot)
    db.commit()
    db.refresh(member_plot)

    return member_plot


def get_voting_representative(
    db: Session,
    plot_id: int,
) -> MemberPlot | None:
    """Текущий совладелец, который голосует за этот участок (если определён)."""
    return db.scalar(
        select(MemberPlot).where(
            MemberPlot.plot_id == plot_id,
            MemberPlot.is_voting_representative.is_(True),
        )
    )


def set_voting_representative(
    db: Session,
    plot_id: int,
    member_id: int,
) -> MemberPlot:
    """
    Явное назначение голосующего по участку.
    Вызывается ADMIN/BOARD (проверка прав — на уровне роутера,
    permission "members.write").
    """
    rows = db.scalars(
        select(MemberPlot).where(MemberPlot.plot_id == plot_id)
    ).all()

    target = next((r for r in rows if r.member_id == member_id), None)

    if target is None:
        raise ValueError(
            "Указанный член не является совладельцем этого участка."
        )

    if target.voting_waived:
        raise ValueError(
            "Этот совладелец ранее отказался от права голоса. "
            "Сначала отмените отказ (unwaive_voting_right)."
        )

    for row in rows:
        row.is_voting_representative = row.member_id == member_id

    db.commit()
    db.refresh(target)

    return target


def waive_voting_right(
    db: Session,
    plot_id: int,
    member_id: int,
) -> MemberPlot:
    """
    Совладелец добровольно отказывается от голоса по участку.
    Если после отказа остаётся ровно один совладелец, не отказавшийся
    от голоса, он автоматически становится представителем — по правилу
    "второй голосует как 1 полный голос".
    Если остаётся 0 или больше 1 не отказавшихся — представителя
    нужно назначить явно (set_voting_representative).
    """
    rows = db.scalars(
        select(MemberPlot).where(MemberPlot.plot_id == plot_id)
    ).all()

    target = next((r for r in rows if r.member_id == member_id), None)

    if target is None:
        raise ValueError(
            "Указанный член не является совладельцем этого участка."
        )

    target.voting_waived = True
    target.is_voting_representative = False

    _resolve_voting_representative(rows)

    db.commit()
    db.refresh(target)

    return target


def unwaive_voting_right(
    db: Session,
    plot_id: int,
    member_id: int,
) -> MemberPlot:
    """Отмена ранее сделанного отказа от голоса."""
    rows = db.scalars(
        select(MemberPlot).where(MemberPlot.plot_id == plot_id)
    ).all()

    target = next((r for r in rows if r.member_id == member_id), None)

    if target is None:
        raise ValueError(
            "Указанный член не является совладельцем этого участка."
        )

    target.voting_waived = False

    # После отмены отказа однозначность может пропасть — пересчитываем.
    for row in rows:
        row.is_voting_representative = False

    _resolve_voting_representative(rows)

    db.commit()
    db.refresh(target)

    return target


def _resolve_voting_representative(rows: list[MemberPlot]) -> None:
    """
    Если среди совладельцев ровно один не отказался от голоса —
    делает его представителем. Иначе оставляет вопрос открытым
    (требуется ручное назначение ADMIN/BOARD).
    Мутирует объекты в rows, не коммитит — коммит на вызывающей стороне.
    """
    active = [r for r in rows if not r.voting_waived]

    if len(active) == 1:
        for row in rows:
            row.is_voting_representative = row is active[0]
