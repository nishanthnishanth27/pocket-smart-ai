import json
import logging
from pathlib import Path

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi import status

from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import COOKIE_NAME
from .auth import create_token
from .auth import get_current_user
from .auth import hash_password
from .auth import verify_password

from .config import get_settings

from .database import Base
from .database import engine
from .database import get_db

from .gemini_service import generate_home
from .gemini_service import generate_jewelry
from .gemini_service import generate_party

from .models import RecommendationHistory
from .models import User

from .schemas import HomeRequest
from .schemas import LoginRequest
from .schemas import PartyRequest
from .schemas import RegisterRequest


BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger("pocketsmart")

settings = get_settings()

if not settings.secret_key or settings.secret_key == "change-this-secret-key":
    logger.warning(
        "SECRET_KEY is not configured. Set it in Vercel Environment Variables."
    )

if not settings.database_url:
    logger.error("DATABASE_URL is missing in the environment.")


# Create database tables.
Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "PocketSmart AI budget and "
        "recommendation assistant."
    ),
)


app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "static"
    ),
    name="static",
)


templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# ---------------------------------------------------------
# HTML PAGES
# ---------------------------------------------------------


@app.get(
    "/",
    response_class=HTMLResponse,
)
def home_page(request: Request):

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user": None,
        },
    )


@app.get(
    "/login",
    response_class=HTMLResponse,
)
def login_page(request: Request):

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "user": None,
        },
    )


@app.get(
    "/register",
    response_class=HTMLResponse,
)
def register_page(request: Request):

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "user": None,
        },
    )


@app.get(
    "/dashboard",
    response_class=HTMLResponse,
)
def dashboard_page(
    request: Request,
    user: User = Depends(get_current_user),
):

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
        },
    )


@app.get(
    "/planner/{kind}",
    response_class=HTMLResponse,
)
def planner_page(
    kind: str,
    request: Request,
    user: User = Depends(get_current_user),
):

    if kind not in {
        "home",
        "party",
        "jewelry",
    }:

        raise HTTPException(
            status_code=404,
            detail="Planner not found",
        )

    if kind == "home":
        template_name = "home_planner.html"

    elif kind == "party":
        template_name = "party.html"

    else:
        template_name = "jewelry.html"

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "user": user,
        },
    )


@app.get(
    "/history",
    response_class=HTMLResponse,
)
def history_page(
    request: Request,
    user: User = Depends(get_current_user),
):

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "user": user,
        },
    )


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------


@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": settings.app_name,
        "gemini_configured": bool(
            settings.gemini_api_key
        ),
    }


# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------


@app.post("/api/auth/register")
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    logger.info(
        "Registration request received for email=%s",
        getattr(payload, "email", "<missing>"),
    )

    try:
        email = payload.email.lower().strip()

        logger.info("Checking existing user for email=%s", email)
        existing_user = db.scalar(
            select(User).where(
                User.email == email
            )
        )

        if existing_user:
            logger.warning("Registration blocked: email already exists - %s", email)
            raise HTTPException(
                status_code=409,
                detail="Email already registered",
            )

        user = User(
            name=payload.name.strip(),
            email=email,
            password_hash=hash_password(
                payload.password
            ),
        )

        logger.info("Creating new user record for %s", email)
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_token(user)

        logger.info("Registration successful for user_id=%s", user.id)

        response = JSONResponse(
            {
                "message": "Registration successful",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                },
            }
        )

        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=(
                settings.access_token_expire_minutes
                * 60
            ),
        )

        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Unhandled registration failure for email=%s",
            getattr(payload, "email", "<missing>"),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {exc.__class__.__name__}: {str(exc)}",
        ) from exc


@app.post("/api/auth/login")
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):

    email = payload.email.lower()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if (
        not user
        or not verify_password(
            payload.password,
            user.password_hash,
        )
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_token(user)

    response = JSONResponse(
        {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            },
        }
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=(
            settings.access_token_expire_minutes
            * 60
        ),
    )

    return response


@app.post("/api/auth/logout")
def logout():

    response = JSONResponse(
        {
            "message": "Logged out"
        }
    )

    response.delete_cookie(
        COOKIE_NAME
    )

    return response


@app.get("/api/auth/me")
def current_user(
    user: User = Depends(get_current_user),
):

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


# ---------------------------------------------------------
# SESSION
# ---------------------------------------------------------


@app.get("/api/session-info")
def session_info(
    user: User = Depends(get_current_user),
):

    return {
        "logged_in": True,
        "user_id": user.id,
        "email": user.email,
    }


@app.get("/api/session-data")
def session_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    rows = db.scalars(
        select(RecommendationHistory).where(
            RecommendationHistory.user_id
            == user.id
        )
    ).all()

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "recommendation_count": len(rows),
    }


# ---------------------------------------------------------
# HISTORY HELPER
# ---------------------------------------------------------


def save_history(
    db: Session,
    user: User,
    planner_type: str,
    request_data: dict,
    result: dict,
):

    row = RecommendationHistory(
        user_id=user.id,
        planner_type=planner_type,
        request_json=json.dumps(
            request_data,
            ensure_ascii=False,
        ),
        result_json=json.dumps(
            result,
            ensure_ascii=False,
        ),
    )

    db.add(row)

    db.commit()

    db.refresh(row)

    return row.id


# ---------------------------------------------------------
# HOME PLANNER
# ---------------------------------------------------------


@app.post("/api/planners/home")
def home_planner(
    payload: HomeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    data = payload.model_dump()

    result = generate_home(data)

    history_id = save_history(
        db=db,
        user=user,
        planner_type="home",
        request_data=data,
        result=result,
    )

    return {
        "history_id": history_id,
        "planner": "home",
        "result": result,
    }


# ---------------------------------------------------------
# PARTY PLANNER
# ---------------------------------------------------------


@app.post("/api/planners/party")
def party_planner(
    payload: PartyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    data = payload.model_dump()

    result = generate_party(data)

    history_id = save_history(
        db=db,
        user=user,
        planner_type="party",
        request_data=data,
        result=result,
    )

    return {
        "history_id": history_id,
        "planner": "party",
        "result": result,
    }


# ---------------------------------------------------------
# JEWELRY PLANNER
# ---------------------------------------------------------


@app.post("/api/planners/jewelry")
async def jewelry_planner(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    form = await request.form()

    budget_value = form.get(
        "budget"
    )

    try:

        budget = float(
            budget_value
        )

    except (
        TypeError,
        ValueError,
    ):

        raise HTTPException(
            status_code=422,
            detail="Budget must be a number",
        )

    if budget <= 0:

        raise HTTPException(
            status_code=422,
            detail="Budget must be positive",
        )

    data = {
        "budget": budget,

        "occasion": str(
            form.get(
                "occasion",
                "Wedding",
            )
        ),

        "style": str(
            form.get(
                "style",
                "Elegant",
            )
        ),

        "city": str(
            form.get(
                "city",
                "Chennai",
            )
        ),
    }

    upload = form.get(
        "outfit_image"
    )

    image_bytes = None

    mime_type = None

    if (
        isinstance(
            upload,
            UploadFile,
        )
        and upload.filename
    ):

        mime_type = upload.content_type

        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }

        if mime_type not in allowed_types:

            raise HTTPException(
                status_code=415,
                detail=(
                    "Use JPG, PNG or WEBP image."
                ),
            )

        image_bytes = await upload.read()

        max_bytes = (
            settings.max_upload_mb
            * 1024
            * 1024
        )

        if len(image_bytes) > max_bytes:

            raise HTTPException(
                status_code=413,
                detail=(
                    "Image is too large."
                ),
            )

    result = generate_jewelry(
        data,
        image_bytes,
        mime_type,
    )

    history_id = save_history(
        db=db,
        user=user,
        planner_type="jewelry",
        request_data=data,
        result=result,
    )

    return {
        "history_id": history_id,
        "planner": "jewelry",
        "result": result,
    }


# ---------------------------------------------------------
# HISTORY
# ---------------------------------------------------------


@app.get("/api/history")
def get_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    rows = db.scalars(
        select(RecommendationHistory)
        .where(
            RecommendationHistory.user_id
            == user.id
        )
        .order_by(
            desc(
                RecommendationHistory.created_at
            )
        )
    ).all()

    return [
        {
            "id": row.id,
            "planner_type": row.planner_type,
            "created_at": (
                row.created_at.isoformat()
                if row.created_at
                else None
            ),
            "request": json.loads(
                row.request_json
            ),
        }
        for row in rows
    ]


@app.get(
    "/api/history/{history_id}"
)
def get_history_detail(
    history_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    row = db.scalar(
        select(
            RecommendationHistory
        ).where(
            RecommendationHistory.id
            == history_id,
            RecommendationHistory.user_id
            == user.id,
        )
    )

    if not row:

        raise HTTPException(
            status_code=404,
            detail="History entry not found",
        )

    return {
        "id": row.id,
        "planner_type": row.planner_type,
        "created_at": (
            row.created_at.isoformat()
            if row.created_at
            else None
        ),
        "request": json.loads(
            row.request_json
        ),
        "result": json.loads(
            row.result_json
        ),
    }


@app.get(
    "/api/recommendations-details/{history_id}"
)
def recommendation_details(
    history_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return get_history_detail(
        history_id,
        user,
        db,
    )


@app.delete(
    "/api/history/{history_id}"
)
def delete_history(
    history_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    row = db.scalar(
        select(
            RecommendationHistory
        ).where(
            RecommendationHistory.id
            == history_id,
            RecommendationHistory.user_id
            == user.id,
        )
    )

    if not row:

        raise HTTPException(
            status_code=404,
            detail="History entry not found",
        )

    db.delete(row)

    db.commit()

    return {
        "message": "Deleted"
    }


# ---------------------------------------------------------
# AUTH ERROR HANDLER
# ---------------------------------------------------------


@app.exception_handler(
    status.HTTP_401_UNAUTHORIZED
)
async def authentication_exception(
    request: Request,
    exc: HTTPException,
):

    if request.url.path.startswith(
        "/api/"
    ):

        return JSONResponse(
            {
                "detail": exc.detail
            },
            status_code=401,
        )

    return RedirectResponse(
        "/login",
        status_code=303,
    )