from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.routes.users import create
from app.schemas.users import UserCreate

client = TestClient(app)


def test_create_user():
    response = client.post(
        "/users/",
        json={"first_name": "Ada", "last_name": "Lovelace"},
    )
    created_id = response.json().get("id")

    try:
        assert response.status_code == 200
        body = response.json()
        assert body["first_name"] == "Ada"
        assert body["last_name"] == "Lovelace"
        assert isinstance(body["id"], int)
        assert body["created_at"]
        assert body["updated_at"]
    finally:
        if created_id is not None:
            client.delete(f"/users/{created_id}")


def test_mocked():
    """Unit-test the POST handler: call create() with a fake session (no HTTP, no DB)."""
    created_at = datetime(2026, 9, 29, tzinfo=timezone.utc)
    session = MagicMock()

    def refresh(user):
        user.id = 1
        user.created_at = created_at
        user.updated_at = created_at

    session.refresh.side_effect = refresh

    payload = UserCreate(first_name="Ada", last_name="Lovelace")
    user = create(payload=payload, db=session)

    assert user.first_name == "Ada"
    assert user.last_name == "Lovelace"
    assert user.id == 1
    assert user.created_at == created_at
    assert user.updated_at == created_at

    session.add.assert_called_once()
    added_user = session.add.call_args.args[0]
    assert added_user.first_name == "Ada"
    assert added_user.last_name == "Lovelace"
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(added_user)
    session.query.assert_not_called()


def test_get_user_by_id():
    # TODO
    pass

def test_get_all_users():
    # TODO
    pass

def test_update_user():
    # TODO
    pass

def test_delete_user():
    # TODO
    pass