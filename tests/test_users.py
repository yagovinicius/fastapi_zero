from http import HTTPStatus

from fastapi.testclient import TestClient

from fastapi_zero.models import User
from fastapi_zero.schemas import UserPublic
from tests.conftest import PayloadBuilder


def test_create_user(
    client: TestClient, build_user_schema: PayloadBuilder
) -> None:
    payload = build_user_schema()

    response = client.post(
        '/api/v1/users',
        json=payload,
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'username': payload['username'],
        'email': payload['email'],
    }


def test_get_users(client: TestClient, user: User, token: str) -> None:
    user_schema = UserPublic.model_validate(user).model_dump(mode='json')

    response = client.get(
        '/api/v1/users',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )

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
    build_user_schema: PayloadBuilder,
) -> None:
    payload = build_user_schema()
    response = client.put(
        f'/api/v1/users/{user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json=payload,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': user.id,
        'username': payload['username'],
        'email': payload['email'],
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
    client: TestClient,
    other_user: User,
    token: str,
    build_user_schema: PayloadBuilder,
) -> None:
    response = client.put(
        f'/api/v1/users/{other_user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json=build_user_schema(),
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
    client: TestClient, user: User, build_user_schema: PayloadBuilder
) -> None:
    response = client.post(
        '/api/v1/users',
        json=build_user_schema(username=user.username),
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Username already exists'


def test_create_user_email_integrity_error(
    client: TestClient, user: User, build_user_schema: PayloadBuilder
) -> None:
    response = client.post(
        '/api/v1/users',
        json=build_user_schema(email=user.email),
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Email already exists'


def test_update_username_integrity_error(
    client: TestClient,
    user: User,
    token: str,
    other_user: User,
    build_user_schema: PayloadBuilder,
) -> None:
    response = client.put(
        f'/api/v1/users/{user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json=build_user_schema(username=other_user.username),
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Username or email already exists'


def test_update_email_integrity_error(
    client: TestClient,
    user: User,
    token: str,
    other_user: User,
    build_user_schema: PayloadBuilder,
) -> None:
    response = client.put(
        f'/api/v1/users/{user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json=build_user_schema(email=other_user.email),
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Username or email already exists'
