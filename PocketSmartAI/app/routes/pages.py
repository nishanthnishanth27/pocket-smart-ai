from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models import RecommendationHistory

router = APIRouter()
BASE = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE / "templates")
settings = get_settings()


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "user": None})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": user}
    )


@router.get("/planner/{kind}", response_class=HTMLResponse)
def planner_page(kind: str, request: Request, user=Depends(get_current_user)):
    if kind not in {"home", "party", "jewelry"}:
        raise HTTPException(404, "Planner not found")
    template = {
        "home": "home_planner.html",
        "party": "party_planner.html",
        "jewelry": "jewelry_planner.html",
    }[kind]
    return templates.TemplateResponse(template, {"request": request, "user": user})


@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "history.html", {"request": request, "user": user}
    )


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "gemini_configured": bool(settings.gemini_api_key),
    }


@router.get("/api/session-info")
def session_info(user=Depends(get_current_user)):
    return {"logged_in": True, "user_id": user.id, "email": user.email}


@router.get("/api/session-data")
def session_data(user=Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.scalar(
        select(func.count())
        .select_from(RecommendationHistory)
        .where(RecommendationHistory.user_id == user.id)
    )
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "recommendation_count": count or 0,
    }
