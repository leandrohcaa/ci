from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.params import PositiveId
from app.models.course import Course
from app.schemas.courses import CourseCreate, CourseRead, CourseUpdate

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/", response_model=list[CourseRead])
def get_all(
    db: Session = Depends(get_db),
) -> list[CourseRead]:
    return db.query(Course).all()


@router.post("/", response_model=CourseRead)
def create(
    payload: CourseCreate,
    db: Session = Depends(get_db),
) -> CourseRead:
    course = Course(
        title=payload.title,
        description=payload.description,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return course


@router.get("/{id}", response_model=CourseRead)
def get_by_id(
    id: PositiveId,
    db: Session = Depends(get_db),
) -> CourseRead:
    course = db.query(Course).get(id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@router.patch("/{id}", response_model=CourseRead)
def update(
    id: PositiveId,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
) -> CourseRead:
    course = db.query(Course).get(id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)

    return course


@router.delete("/{id}")
def delete(
    id: PositiveId,
    db: Session = Depends(get_db),
) -> dict:
    course = db.query(Course).get(id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()

    return {"detail": "Course deleted"}
