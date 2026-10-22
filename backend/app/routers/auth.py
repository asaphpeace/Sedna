import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.org_structure import Department
from app.models.user import Organisation, User
from app.schemas.auth import (
    AcceptInviteRequest, ChangePasswordRequest, ForgotPasswordRequest, GoogleSignInRequest, InviteInfo, LoginRequest,
    ResetPasswordRequest, TokenData, TokenResponse,
)
from app.schemas.user import UserOut
from app.services.auth import authenticate_user, create_access_token, hash_password, verify_password
from app.services.deps import current_user
from app.services.email import send_password_reset_email
from app.services.google_sign_in import user_for_google, verify_google_token

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

RESET_TOKEN_TTL = timedelta(hours=1)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(TokenData(user_id=user.id, org_id=user.org_id))
    return TokenResponse(access_token=token)


@router.post("/change-password", status_code=204)
@limiter.limit("10/minute")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    # Rate-limited like sign-in, since a wrong current password is a guess
    if not user.password_hash or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your current password is incorrect.")
    if body.new_password == body.current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a password different from your current one.")
    user.password_hash = hash_password(body.new_password)
    await db.commit()


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    out = UserOut.model_validate(user)
    if not user.is_admin:
        result = await db.execute(select(Department).where(Department.manager_user_id == user.id))
        out.is_manager = result.scalars().first() is not None
    org = await db.get(Organisation, user.org_id)
    out.is_sedna_staff = bool(org and org.kind == "sedna")
    return out


async def _find_valid_invite(db: AsyncSession, token: str) -> User:
    result = await db.execute(select(User).where(User.invite_token == token))
    invite = result.scalar_one_or_none()
    if not invite or invite.status != "invited":
        raise HTTPException(status_code=404, detail="Invite not found or already used")
    if not invite.invite_token_expires_at or invite.invite_token_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite link has expired — ask for a new one")
    return invite


@router.get("/invite/{token}", response_model=InviteInfo)
async def get_invite(token: str, db: AsyncSession = Depends(get_db)):
    invite = await _find_valid_invite(db, token)
    org_result = await db.execute(select(Organisation).where(Organisation.id == invite.org_id))
    org = org_result.scalar_one_or_none()
    return InviteInfo(name=invite.name, email=invite.email, org_name=org.name if org else "your team")


@router.post("/accept-invite", response_model=TokenResponse)
async def accept_invite(body: AcceptInviteRequest, db: AsyncSession = Depends(get_db)):
    invite = await _find_valid_invite(db, body.token)
    invite.password_hash = hash_password(body.password)
    invite.status = "active"
    invite.invite_token = None
    invite.invite_token_expires_at = None
    await db.commit()

    token = create_access_token(TokenData(user_id=invite.id, org_id=invite.org_id))
    return TokenResponse(access_token=token)


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/forgot-password", status_code=202)
@limiter.limit("5/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    # Same answer whether or not the email has an account, so the form can't be
    # used to find out who is registered.
    result = await db.execute(select(User).where(func.lower(User.email) == body.email.lower()))
    user = result.scalar_one_or_none()
    if user and user.status == "active":
        token = secrets.token_urlsafe(32)
        user.reset_token_hash = _hash_reset_token(token)
        user.reset_token_expires_at = datetime.utcnow() + RESET_TOKEN_TTL
        await db.commit()
        await send_password_reset_email(user.email, user.name, token)
    return {"detail": "If an account exists for that email, a reset link is on its way."}


async def _find_valid_reset(db: AsyncSession, token: str) -> User:
    result = await db.execute(select(User).where(User.reset_token_hash == _hash_reset_token(token)))
    user = result.scalar_one_or_none()
    if (not user or user.status != "active" or not user.reset_token_expires_at
            or user.reset_token_expires_at < datetime.utcnow()):
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired. Ask for a new one.")
    return user


@router.get("/reset-password/{token}", status_code=204)
@limiter.limit("20/minute")
async def check_reset(request: Request, token: str, db: AsyncSession = Depends(get_db)):
    await _find_valid_reset(db, token)


@router.post("/reset-password", response_model=TokenResponse)
@limiter.limit("10/minute")
async def reset_password(request: Request, body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    user = await _find_valid_reset(db, body.token)
    user.password_hash = hash_password(body.password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    await db.commit()
    token = create_access_token(TokenData(user_id=user.id, org_id=user.org_id))
    return TokenResponse(access_token=token)


@router.get("/config")
async def auth_config():
    """What the sign-in page offers. Public: the Google client ID isn't secret."""
    return {"google_client_id": settings.google_client_id or None}


@router.post("/google", response_model=TokenResponse)
@limiter.limit("10/minute")
async def google_sign_in(request: Request, body: GoogleSignInRequest, db: AsyncSession = Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(status_code=404, detail="Google sign-in isn't switched on.")
    claims = await verify_google_token(body.credential)
    user = await user_for_google(db, claims)
    token = create_access_token(TokenData(user_id=user.id, org_id=user.org_id))
    return TokenResponse(access_token=token)
