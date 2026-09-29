from fastapi.testclient import TestClient

from app.main import app
from app.models.enrollment import MAX_COURSES_PER_USER, MAX_USERS_PER_COURSE

client = TestClient(app)


def create_user(first_name: str, last_name: str = "Student") -> int:
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


def test_enroll_list_get_and_delete():
    user_id = create_user("Ada")
    course_id = create_course("Algebra")

    try:
        created = client.post(
            "/enrollments/",
            json={"user_id": user_id, "course_id": course_id},
        )
        assert created.status_code == 200
        enrollment_id = created.json()["id"]
        assert created.json()["user_id"] == user_id
        assert created.json()["course_id"] == course_id

        listed = client.get("/enrollments/", params={"user_id": user_id})
        assert listed.status_code == 200
        assert [item["id"] for item in listed.json()] == [enrollment_id]

        fetched = client.get(f"/enrollments/{enrollment_id}")
        assert fetched.status_code == 200
        assert fetched.json()["course_id"] == course_id

        deleted = client.delete(f"/enrollments/{enrollment_id}")
        assert deleted.status_code == 200
        assert deleted.json()["detail"] == "Enrollment deleted"
        assert client.get(f"/enrollments/{enrollment_id}").status_code == 404
    finally:
        client.delete(f"/users/{user_id}")
        client.delete(f"/courses/{course_id}")


def test_duplicate_enrollment_is_rejected():
    user_id = create_user("Grace")
    course_id = create_course("Chemistry")

    try:
        first = client.post(
            "/enrollments/",
            json={"user_id": user_id, "course_id": course_id},
        )
        assert first.status_code == 200

        second = client.post(
            "/enrollments/",
            json={"user_id": user_id, "course_id": course_id},
        )
        assert second.status_code == 409
    finally:
        client.delete(f"/users/{user_id}")
        client.delete(f"/courses/{course_id}")


def test_user_cannot_enroll_in_more_than_five_courses():
    user_id = create_user("Alan")
    course_ids = [
        create_course(f"User limit {index}")
        for index in range(MAX_COURSES_PER_USER + 1)
    ]

    try:
        for course_id in course_ids[:MAX_COURSES_PER_USER]:
            response = client.post(
                "/enrollments/",
                json={"user_id": user_id, "course_id": course_id},
            )
            assert response.status_code == 200

        rejected = client.post(
            "/enrollments/",
            json={"user_id": user_id, "course_id": course_ids[-1]},
        )
        assert rejected.status_code == 409

        removed = client.get("/enrollments/", params={"user_id": user_id}).json()[0]
        assert client.delete(f"/enrollments/{removed['id']}").status_code == 200

        retried = client.post(
            "/enrollments/",
            json={"user_id": user_id, "course_id": course_ids[-1]},
        )
        assert retried.status_code == 200
    finally:
        client.delete(f"/users/{user_id}")
        for course_id in course_ids:
            client.delete(f"/courses/{course_id}")


def test_course_cannot_have_more_than_twenty_users():
    course_id = create_course("Packed seminar")
    user_ids = [
        create_user(f"Student{index}") for index in range(MAX_USERS_PER_COURSE + 1)
    ]

    try:
        for user_id in user_ids[:MAX_USERS_PER_COURSE]:
            response = client.post(
                "/enrollments/",
                json={"user_id": user_id, "course_id": course_id},
            )
            assert response.status_code == 200

        rejected = client.post(
            "/enrollments/",
            json={"user_id": user_ids[-1], "course_id": course_id},
        )
        assert rejected.status_code == 409
    finally:
        for user_id in user_ids:
            client.delete(f"/users/{user_id}")
        client.delete(f"/courses/{course_id}")


def test_enroll_missing_user_or_course():
    user_id = create_user("Katherine")
    course_id = create_course("Physics")

    try:
        missing_user = client.post(
            "/enrollments/",
            json={"user_id": 999999999, "course_id": course_id},
        )
        assert missing_user.status_code == 404

        missing_course = client.post(
            "/enrollments/",
            json={"user_id": user_id, "course_id": 999999999},
        )
        assert missing_course.status_code == 404

        invalid = client.post(
            "/enrollments/",
            json={"user_id": 0, "course_id": course_id},
        )
        assert invalid.status_code == 422
    finally:
        client.delete(f"/users/{user_id}")
        client.delete(f"/courses/{course_id}")
