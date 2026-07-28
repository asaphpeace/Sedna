from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.org_structure import Department
from app.models.user import Organisation, User
from app.schemas.auth import AcceptInviteRequest, InviteInfo, LoginRequest, TokenData, TokenResponse
from app.schemas.user import UserOut
from app.services.auth import authenticate_user, create_access_token, hash_password
from app.services.deps import current_user

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


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


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    out = UserOut.model_validate(user)
    if not user.is_admin:
        result = await db.execute(select(Department).where(Department.manager_user_id == user.id))
        out.is_manager = result.scalars().first() is not None
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
