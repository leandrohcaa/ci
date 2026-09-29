from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_async import get_async_db
from app.core.params import PositiveId
from app.models.user import User
from app.schemas.users import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users-async"])


@router.patch("/{id}/async", response_model=UserRead)
async def update_user_async(
    id: PositiveId,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
) -> UserRead:
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user
