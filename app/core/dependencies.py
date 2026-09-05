from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.core.permissions import has_permission
from app.modules.users.models import Role, User
from app.modules.users.service import get_session


def current_user(
    session_token: str | None = Cookie(default=None),
) -> User | None:
    if not session_token:
        return None

    db = SessionLocal()

    try:
        session = get_session(db, session_token)

        if session is None:
            return None

        user = db.scalar(
            select(User)
            .options(
                selectinload(User.roles)
                .selectinload(Role.permissions)
            )
            .where(User.id == session.user_id)
        )

        if user is None or not user.is_active:
            return None

        return user

    finally:
        db.close()


def require_permission(permission_code: str):
    def dependency(
        user: User | None = Depends(current_user),
    ) -> User:
        if user is None:
            raise HTTPException(
                status_code=303,
                headers={"Location": "/login"},
            )

        if not has_permission(user, permission_code):
            raise HTTPException(
                status_code=403,
                detail="Доступ запрещён",
            )

        return user

    return dependency


def get_db():
    """Зависимость для роутеров: сессия БД с гарантированным закрытием."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
