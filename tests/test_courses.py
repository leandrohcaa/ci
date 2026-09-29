from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.routes.courses import create
from app.schemas.courses import CourseCreate

client = TestClient(app)


def test_create_course():
    response = client.post(
        "/courses/",
        json={"title": "Algebra", "description": "Introductory algebra"},
    )
    created_id = response.json().get("id")

    try:
        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Algebra"
        assert body["description"] == "Introductory algebra"
        assert isinstance(body["id"], int)
        assert body["created_at"]
        assert body["updated_at"]
    finally:
        if created_id is not None:
            client.delete(f"/courses/{created_id}")


def test_course_crud():
    created = client.post(
        "/courses/",
        json={"title": "  Biology  ", "description": "  Cells and organisms  "},
    )
    assert created.status_code == 200
    course_id = created.json()["id"]

    try:
        assert created.json()["title"] == "Biology"
        assert created.json()["description"] == "Cells and organisms"

        listed = client.get("/courses/")
        assert listed.status_code == 200
        assert any(item["id"] == course_id for item in listed.json())

        fetched = client.get(f"/courses/{course_id}")
        assert fetched.status_code == 200
        assert fetched.json()["title"] == "Biology"

        updated = client.patch(
            f"/courses/{course_id}",
            json={"title": "Advanced Biology"},
        )
        assert updated.status_code == 200
        assert updated.json()["title"] == "Advanced Biology"
        assert updated.json()["description"] == "Cells and organisms"
    finally:
        deleted = client.delete(f"/courses/{course_id}")
        assert deleted.status_code == 200
        assert deleted.json()["detail"] == "Course deleted"

    missing = client.get(f"/courses/{course_id}")
    assert missing.status_code == 404


def test_create_course_rejects_blank_title():
    response = client.post(
        "/courses/",
        json={"title": "   ", "description": "A real description"},
    )
    assert response.status_code == 422


def test_update_course_rejects_null_title():
    created = client.post(
        "/courses/",
        json={"title": "History", "description": "World history"},
    )
    course_id = created.json()["id"]

    try:
        response = client.patch(f"/courses/{course_id}", json={"title": None})
        assert response.status_code == 422
    finally:
        client.delete(f"/courses/{course_id}")


def test_mocked_create_course():
    created_at = datetime(2026, 9, 29, tzinfo=timezone.utc)
    session = MagicMock()

    def refresh(course):
        course.id = 1
        course.created_at = created_at
        course.updated_at = created_at

    session.refresh.side_effect = refresh

    payload = CourseCreate(title="Algebra", description="Introductory algebra")
    course = create(payload=payload, db=session)

    assert course.title == "Algebra"
    assert course.description == "Introductory algebra"
    assert course.id == 1
    assert course.created_at == created_at
    assert course.updated_at == created_at

    session.add.assert_called_once()
    added_course = session.add.call_args.args[0]
    assert added_course.title == "Algebra"
    assert added_course.description == "Introductory algebra"
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(added_course)
    session.query.assert_not_called()
