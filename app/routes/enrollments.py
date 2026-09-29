from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.params import POSTGRES_INT_MAX, PositiveId
from app.models.course import Course
from app.models.enrollment import MAX_COURSES_PER_USER, MAX_USERS_PER_COURSE, Enrollment
from app.models.user import User
from app.schemas.enrollments import EnrollmentCreate, EnrollmentRead

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.get("/", response_model=list[EnrollmentRead])
def get_all(
    user_id: int | None = Query(default=None, gt=0, le=POSTGRES_INT_MAX),
    course_id: int | None = Query(default=None, gt=0, le=POSTGRES_INT_MAX),
    db: Session = Depends(get_db),
) -> list[EnrollmentRead]:
    query = db.query(Enrollment)
    if user_id is not None:
        query = query.filter(Enrollment.user_id == user_id)
    if course_id is not None:
        query = query.filter(Enrollment.course_id == course_id)
    return query.all()


@router.post("/", response_model=EnrollmentRead)
def create(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db),
) -> EnrollmentRead:
    user = (
        db.query(User)
        .filter(User.id == payload.user_id)
        .with_for_update()
        .one_or_none()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    course = (
        db.query(Course)
        .filter(Course.id == payload.course_id)
        .with_for_update()
        .one_or_none()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    already_enrolled = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == payload.user_id,
            Enrollment.course_id == payload.course_id,
        )
        .one_or_none()
    )
    if already_enrolled:
        raise HTTPException(
            status_code=409, detail="User is already enrolled in this course"
        )

    user_course_count = (
        db.query(Enrollment).filter(Enrollment.user_id == payload.user_id).count()
    )
    if user_course_count >= MAX_COURSES_PER_USER:
        raise HTTPException(
            status_code=409,
            detail=f"A user can be enrolled in up to {MAX_COURSES_PER_USER} courses",
        )

    course_user_count = (
        db.query(Enrollment).filter(Enrollment.course_id == payload.course_id).count()
    )
    if course_user_count >= MAX_USERS_PER_COURSE:
        raise HTTPException(
            status_code=409,
            detail=f"A course can have up to {MAX_USERS_PER_COURSE} users",
        )

    enrollment = Enrollment(user_id=payload.user_id, course_id=payload.course_id)
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="User is already enrolled in this course"
        )
    db.refresh(enrollment)

    return enrollment


@router.get("/{id}", response_model=EnrollmentRead)
def get_by_id(
    id: PositiveId,
    db: Session = Depends(get_db),
) -> EnrollmentRead:
    enrollment = db.query(Enrollment).get(id)

    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    return enrollment


@router.delete("/{id}")
def delete(
    id: PositiveId,
    db: Session = Depends(get_db),
) -> dict:
    enrollment = db.query(Enrollment).get(id)

    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    db.delete(enrollment)
    db.commit()

    return {"detail": "Enrollment deleted"}
