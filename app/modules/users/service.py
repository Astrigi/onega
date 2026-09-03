import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.modules.users.session import Session


SESSION_TTL_DAYS = 7


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db, user_id: int) -> tuple[str, Session]:
    token = secrets.token_urlsafe(48)
    token_hash = _hash_token(token)

    session = Session(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=SESSION_TTL_DAYS),
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return token, session


def get_session(db, token: str) -> Session | None:
    token_hash = _hash_token(token)

    session = db.scalar(
        select(Session).where(
            Session.token_hash == token_hash,
            Session.revoked_at.is_(None),
            Session.expires_at > datetime.now(timezone.utc),
        )
    )

    return session


def revoke_session(db, token: str) -> bool:
    session = get_session(db, token)

    if session is None:
        return False

    session.revoked_at = datetime.now(timezone.utc)

    db.commit()

    return True


def cleanup_sessions(db) -> int:
    result = db.execute(
        delete(Session).where(
            Session.expires_at <= datetime.now(timezone.utc)
        )
    )

    db.commit()

    return result.rowcount
