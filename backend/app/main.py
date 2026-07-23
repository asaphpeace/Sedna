from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import (
    activity,
    admin,
    analytics,
    auth,
    certificates,
    compliance,
    gamification,
    modules,
    notifications,
    paths,
    progress,
    releases,
    quizzes,
    saved,
    settings as settings_router,
    social,
    team,
    uploads,
    webhooks,
)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Sedna Academy API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(paths.router)
app.include_router(modules.router)
app.include_router(progress.router)
app.include_router(certificates.router)
app.include_router(saved.router)
app.include_router(activity.router)
app.include_router(team.router)
app.include_router(releases.router)
app.include_router(settings_router.router)
app.include_router(quizzes.router)
app.include_router(gamification.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(social.router)
app.include_router(compliance.router)
app.include_router(webhooks.router)
app.include_router(uploads.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}
