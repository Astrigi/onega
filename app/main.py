from fastapi import FastAPI, Request, Form, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.db.session import SessionLocal
from app.core.security import verify_password
from app.core.dependencies import require_permission
from app.modules.users.models import User
from app.modules.users.service import create_session, revoke_session
from app.modules.members.router import router as members_router
from app.modules.plots.router import router as plots_router


app = FastAPI(
    title="СНТ ОНЕГА",
    version="0.1.0",
)

app.include_router(members_router)
app.include_router(plots_router)

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
