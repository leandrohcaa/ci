from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import DataError, IntegrityError, OperationalError

from app.core.errors import register_exception_handlers
from app.main import app
from app.models.enrollment import MAX_COURSES_PER_USER

client = TestClient(app)


def create_user(first_name: str = "Ada", last_name: str = "Lovelace") -> int:
    response = client.post(
        "/users/",
        json={"first_name": first_name, "last_name": last_name},
    )
    assert response.status_code == 200
    return response.json()["id"]


def create_course(title: str) -> int:
    response = client.post(
        "/courses/",
        json={"title": title, "description": "Course description"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_missing_resources_return_a_clear_message():
    missing_user = client.get("/users/999999999")
    assert missing_user.status_code == 404
    assert missing_user.json() == {"detail": "User not found"}

    missing_update = client.patch("/users/999999999", json={"first_name": "Ada"})
    assert missing_update.status_code == 404
    assert missing_update.json() == {"detail": "User not found"}

    missing_delete = client.delete("/users/999999999")
    assert missing_delete.status_code == 404

    missing_course = client.get("/courses/999999999")
    assert missing_course.status_code == 404
    assert missing_course.json() == {"detail": "Course not found"}

    missing_enrollment = client.get("/enrollments/999999999")
    assert missing_enrollment.status_code == 404
    assert missing_enrollment.json() == {"detail": "Enrollment not found"}

    missing_async = client.patch("/users/999999999/async", json={"first_name": "Ada"})
    assert missing_async.status_code == 404
    assert missing_async.json() == {"detail": "User not found"}


def test_invalid_ids_explain_what_is_wrong():
    zero = client.get("/users/0")
    assert zero.status_code == 422
    assert zero.json()["detail"] == "Invalid request"
    assert zero.json()["errors"][0]["field"] == "path.id"
    assert zero.json()["errors"][0]["message"] == "Must be greater than 0"

    negative = client.get("/courses/-1")
    assert negative.status_code == 422

    text = client.get("/enrollments/abc")
    assert text.status_code == 422
    assert text.json()["errors"][0]["message"] == "Must be an integer"

    huge = client.get("/users/9999999999")
    assert huge.status_code == 422
    assert "less than or equal" in huge.json()["errors"][0]["message"]


def test_validation_errors_name_each_field():
    response = client.post("/users/", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Invalid request"
    fields = {error["field"]: error["message"] for error in body["errors"]}
    assert fields["body.first_name"] == "This field is required"
    assert fields["body.last_name"] == "This field is required"


def test_blank_and_unknown_fields_are_rejected():
    blank = client.post(
        "/courses/",
        json={"title": "   ", "description": "A real description"},
    )
    assert blank.status_code == 422
    assert blank.json()["errors"][0]["message"] == "Must not be empty"

    unknown = client.post(
        "/users/",
        json={"first_name": "Ada", "last_name": "Lovelace", "nickname": "A"},
    )
    assert unknown.status_code == 422
    assert unknown.json()["errors"][0]["field"] == "body.nickname"
    assert unknown.json()["errors"][0]["message"] == "Unknown field"


def test_empty_update_and_null_fields_are_rejected():
    user_id = create_user()
    course_id = create_course("History")

    try:
        empty_user = client.patch(f"/users/{user_id}", json={})
        assert empty_user.status_code == 422
        assert any(
            error["message"] == "At least one field must be provided"
            for error in empty_user.json()["errors"]
        )

        null_name = client.patch(f"/users/{user_id}", json={"first_name": None})
        assert null_name.status_code == 422
        assert any(
            error["message"] == "first_name cannot be null"
            for error in null_name.json()["errors"]
        )

        empty_course = client.patch(f"/courses/{course_id}", json={})
        assert empty_course.status_code == 422
    finally:
        client.delete(f"/users/{user_id}")
        client.delete(f"/courses/{course_id}")


def test_malformed_json_is_rejected():
    response = client.post(
        "/users/",
        content=b"{",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["errors"][0]["message"] == "Request body must be valid JSON"


def test_enrollment_conflicts_explain_the_rule():
    user_id = create_user("Grace")
    course_ids = [
        create_course(f"Error course {index}")
        for index in range(MAX_COURSES_PER_USER + 1)
    ]

    try:
        first = client.post(
            "/enrollments/",
            json={"user_id": user_id, "course_id": course_ids[0]},
        )
        assert first.status_code == 200

        duplicate = client.post(
            "/enrollments/",
            json={"user_id": user_id, "course_id": course_ids[0]},
        )
        assert duplicate.status_code == 409
        assert duplicate.json() == {"detail": "User is already enrolled in this course"}

        for course_id in course_ids[1:MAX_COURSES_PER_USER]:
            assert (
                client.post(
                    "/enrollments/",
                    json={"user_id": user_id, "course_id": course_id},
                ).status_code
                == 200
            )

        over_limit = client.post(
            "/enrollments/",
            json={"user_id": user_id, "course_id": course_ids[-1]},
        )
        assert over_limit.status_code == 409
        assert (
            over_limit.json()["detail"] == "A user can be enrolled in up to 5 courses"
        )

        missing_user = client.post(
            "/enrollments/",
            json={"user_id": 999999999, "course_id": course_ids[0]},
        )
        assert missing_user.status_code == 404
        assert missing_user.json() == {"detail": "User not found"}
    finally:
        client.delete(f"/users/{user_id}")
        for course_id in course_ids:
            client.delete(f"/courses/{course_id}")


def test_unexpected_errors_hide_internal_details():
    probe = FastAPI()
    register_exception_handlers(probe)

    @probe.get("/boom")
    def boom():
        raise RuntimeError("secret connection string")

    @probe.get("/conflict")
    def conflict():
        raise IntegrityError("INSERT", {}, Exception("duplicate key users_pkey"))

    @probe.get("/bad-data")
    def bad_data():
        raise DataError("INSERT", {}, Exception("integer out of range"))

    @probe.get("/down")
    def down():
        raise OperationalError("SELECT", {}, Exception("connection refused"))

    probe_client = TestClient(probe, raise_server_exceptions=False)

    unexpected = probe_client.get("/boom")
    assert unexpected.status_code == 500
    assert unexpected.json() == {"detail": "An unexpected error occurred"}
    assert "secret" not in unexpected.text

    conflict_response = probe_client.get("/conflict")
    assert conflict_response.status_code == 409
    assert conflict_response.json() == {
        "detail": "This operation conflicts with existing data"
    }
    assert "users_pkey" not in conflict_response.text

    invalid = probe_client.get("/bad-data")
    assert invalid.status_code == 422
    assert invalid.json() == {"detail": "Invalid data"}

    unavailable = probe_client.get("/down")
    assert unavailable.status_code == 503
    assert unavailable.json() == {
        "detail": "The database is unavailable. Try again later."
    }
