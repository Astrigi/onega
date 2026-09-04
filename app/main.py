from fastapi import FastAPI, Request, Form, Depends, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.core.security import verify_password
from app.core.permissions import has_permission
from app.modules.users.models import User, Role
from app.modules.users.service import create_session, get_session, revoke_session


app = FastAPI(
    title="СНТ ОНЕГА",
    version="0.1.0",
)

templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def public_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="public.html",
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
    )


@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
):
    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(User.username == username)
        )

        if user is None or not user.is_active:
            return {
                "status": "error",
                "message": "Неверный логин или пароль",
            }

        if not verify_password(password, user.password_hash):
            return {
                "status": "error",
                "message": "Неверный логин или пароль",
            }

        token, session = create_session(db, user.id)

        response = RedirectResponse(
            url="/dashboard",
            status_code=303,
        )

        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
        )

        return response

    finally:
        db.close()


@app.post("/logout")
def logout(
    session_token: str | None = Cookie(default=None),
):
    db = SessionLocal()

    try:
        if session_token:
            revoke_session(db, session_token)

        response = RedirectResponse(
            url="/login",
            status_code=303,
        )

        response.delete_cookie(
            key="session_token",
        )

        return response

    finally:
        db.close()


def current_user(
    session_token: str | None = Cookie(default=None),
):
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
    ):
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


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(require_permission("dashboard.read")),
):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
        },
    )
