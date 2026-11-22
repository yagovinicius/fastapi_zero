from http import HTTPStatus

from fastapi.testclient import TestClient

from fastapi_zero.models import User
from fastapi_zero.schemas import UserPublic
from tests.conftest import MockDbTime, UserSchemaFactory


def test_create_user(client: TestClient, mock_db_time: MockDbTime) -> None:
    with mock_db_time(model=User) as (time_post, _time_put):
        user_schema = UserSchemaFactory.build()

        response = client.post(
            '/api/v1/users',
            json=user_schema.model_dump(mode='json'),
        )

    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.json()['id'], int)
    assert response.json()['id'] >= 1
    assert response.json() == {
        'id': response.json()['id'],
        'username': user_schema.username,
        'email': user_schema.email,
        'created_at': time_post.isoformat(),
        'updated_at': time_post.isoformat(),
    }


def test_get_users(client: TestClient, user: User, token: str) -> None:
    user_schema = UserPublic.model_validate(user).model_dump(mode='json')

    response = client.get(
        '/api/v1/users',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': [user_schema]}


def test_get_user_by_id(client: TestClient, user: User, token: str) -> None:
    user_schema = UserPublic.model_validate(user).model_dump(mode='json')

    response = client.get(
        f'/api/v1/users/{user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == user_schema


def test_get_user_by_id_not_found(
    client: TestClient, user: User, token: str
) -> None:
    response = client.get(
        f'/api/v1/users/{user.id + 1}',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'User not found'


def test_update_user(
    client: TestClient,
    user: User,
    token: str,
    mock_db_time: MockDbTime,
) -> None:
    with mock_db_time(model=User) as (_time_post, time_put):
        changes = UserSchemaFactory.build()

        response = client.put(
            f'/api/v1/users/{user.id}',
            headers={
                'Authorization': f'Bearer {token}',
            },
            json=changes.model_dump(mode='json'),
        )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': user.id,
        'username': changes.username,
        'email': changes.email,
        'created_at': user.created_at.isoformat(),
        'updated_at': time_put.isoformat(),
    }


def test_delete_user(client: TestClient, token: str, user: User) -> None:
    response = client.delete(
        f'/api/v1/users/{user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['message'] == 'user has been deleted'


def test_update_user_wrong_user(
    client: TestClient, other_user: User, token: str
) -> None:
    changes = UserSchemaFactory.build()
    response = client.put(
        f'/api/v1/users/{other_user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json=changes.model_dump(mode='json'),
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()['detail'] == 'Not enough permission'


def test_delete_user_wrong_user(
    client: TestClient, other_user: User, token: str
) -> None:
    response = client.delete(
        f'/api/v1/users/{other_user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()['detail'] == 'Not enough permission'


def test_create_user_username_integrity_error(
    client: TestClient, user: User
) -> None:
    user_schema = UserSchemaFactory.build(username=user.username)

    response = client.post(
        '/api/v1/users',
        json=user_schema.model_dump(mode='json'),
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Username already exists'


def test_create_user_email_integrity_error(
    client: TestClient, user: User
) -> None:
    user_schema = UserSchemaFactory.build(email=user.email)

    response = client.post(
        '/api/v1/users',
        json=user_schema.model_dump(mode='json'),
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Email already exists'


def test_update_username_integrity_error(
    client: TestClient, user: User, token: str, other_user: User
) -> None:
    changes = UserSchemaFactory.build(username=other_user.username)

    response = client.put(
        f'/api/v1/users/{user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json=changes.model_dump(mode='json'),
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Username or email already exists'


def test_update_email_integrity_error(
    client: TestClient, user: User, token: str, other_user: User
) -> None:
    changes = UserSchemaFactory.build(email=other_user.email)

    response = client.put(
        f'/api/v1/users/{user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json=changes.model_dump(mode='json'),
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Username or email already exists'
