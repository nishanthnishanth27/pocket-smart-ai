import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models import RecommendationHistory, User
from ..schemas import HomeRequest, PartyRequest
from ..services.recommendation_service import (
    generate_recommendation,
    save_recommendation,
)

router = APIRouter(tags=["recommendations"])
settings = get_settings()


def _create_plan(kind: str, payload, user: User, db: Session) -> dict:
    data = payload.model_dump()
    result = generate_recommendation(kind, data)
    history_id = save_recommendation(db, user, kind, data, result)
    return {"history_id": history_id, "planner": kind, "result": result}


@router.post("/api/planners/home")
def home_planner(
    payload: HomeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _create_plan("home", payload, user, db)


@router.post("/api/planners/party")
def party_planner(
    payload: PartyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _create_plan("party", payload, user, db)


@router.post("/api/planners/jewelry")
async def jewelry_planner(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    form = await request.form()
    try:
        budget = float(form.get("budget"))
    except (TypeError, ValueError):
        raise HTTPException(422, "Budget must be a number")
    if budget <= 0:
        raise HTTPException(422, "Budget must be positive")

    data = {
        "budget": budget,
        "occasion": str(form.get("occasion", "Wedding")),
        "style": str(form.get("style", "Elegant")),
        "city": str(form.get("city", "Chennai")),
    }
    upload = form.get("outfit_image")
    image_bytes = None
    mime_type = None
    if upload and hasattr(upload, "read") and getattr(upload, "filename", ""):
        mime_type = getattr(upload, "content_type", "")
        if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(415, "Use JPG, PNG or WEBP")
        image_bytes = await upload.read()
        if len(image_bytes) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, "Image is too large")

    result = generate_recommendation("jewelry", data, image_bytes, mime_type)
    history_id = save_recommendation(db, user, "jewelry", data, result)
    return {"history_id": history_id, "planner": "jewelry", "result": result}


@router.get("/api/history")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(RecommendationHistory)
        .where(RecommendationHistory.user_id == user.id)
        .order_by(desc(RecommendationHistory.created_at))
    ).all()
    return [
        {
            "id": row.id,
            "planner_type": row.planner_type,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "request": json.loads(row.request_json),
        }
        for row in rows
    ]


@router.get("/api/history/{history_id}")
def history_detail(
    history_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(
        select(RecommendationHistory).where(
            RecommendationHistory.id == history_id,
            RecommendationHistory.user_id == user.id,
        )
    )
    if not row:
        raise HTTPException(404, "History entry not found")
    return {
        "id": row.id,
        "planner_type": row.planner_type,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "request": json.loads(row.request_json),
        "result": json.loads(row.result_json),
    }


@router.get("/api/recommendations-details/{history_id}")
def recommendation_details(
    history_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return history_detail(history_id, user, db)


@router.delete("/api/history/{history_id}")
def delete_history(
    history_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(
        select(RecommendationHistory).where(
            RecommendationHistory.id == history_id,
            RecommendationHistory.user_id == user.id,
        )
    )
    if not row:
        raise HTTPException(404, "History entry not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}
