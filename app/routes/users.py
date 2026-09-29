from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.params import PositiveId
from app.models.user import User
from app.schemas.users import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
def get_all(
    db: Session = Depends(get_db),
) -> list[UserRead]:
    return db.query(User).all()


@router.post("/", response_model=UserRead)
def create(
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> UserRead:
    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/{id}", response_model=UserRead)
def get_by_id(
    id: PositiveId,
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.query(User).get(id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.patch("/{id}", response_model=UserRead)
def update(
    id: PositiveId,
    payload: UserUpdate,
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.query(User).get(id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


@router.delete("/{id}")
def delete(
    id: PositiveId,
    db: Session = Depends(get_db),
) -> dict:
    user = db.query(User).get(id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"detail": "User deleted"}
