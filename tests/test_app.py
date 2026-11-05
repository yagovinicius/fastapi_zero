from http import HTTPStatus

from fastapi.testclient import TestClient

from fastapi_zero.models import User
from fastapi_zero.schemas import UserPublic


def test_root_deve_retornar_ok_e_ola_mundo(client: TestClient) -> None:
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Olá, mundo!'}


def test_create_user(client: TestClient) -> None:
    response = client.post(
        '/users',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'username': 'alice',
        'email': 'alice@example.com',
    }


def test_read_users(client: TestClient) -> None:
    response = client.get('/users')
    assert response.status_code == HTTPStatus.OK

    assert response.json() == {'users': []}


def test_read_users_with_users(client: TestClient, user: User) -> None:
    user_schema = UserPublic.model_validate(user).model_dump(mode='json')

    response = client.get('/users')

    assert response.json() == {'users': [user_schema]}


def test_get_user_by_id(client: TestClient, user: User) -> None:
    user_schema = UserPublic.model_validate(user).model_dump(mode='json')

    response = client.get(f'/users/{user.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == user_schema


def test_get_user_by_id_not_found(client: TestClient, user: User) -> None:
    response = client.get(f'/users/{user.id + 1}')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'user not found'


def test_update_user(client: TestClient, user: User) -> None:
    response = client.put(
        '/users/1',
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': 1,
        'username': 'bob',
        'email': 'bob@example.com',
    }


def test_delete_user(client: TestClient, user: User) -> None:
    response = client.delete('/users/1')
    assert response.status_code == HTTPStatus.OK
    assert response.json()['message'] == 'user has been deleted'


def test_update_user_not_found(client: TestClient) -> None:
    response = client.put(
        '/users/1',
        json={
            'username': 'test',
            'email': 'test@example.com',
            'password': '123',
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_user_not_found(client: TestClient) -> None:
    response = client.delete('/users/1')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_user_username_integrity_error(
    client: TestClient, user: User
) -> None:
    response = client.post(
        '/users',
        json={
            'username': user.username,
            'email': 'new@example.com',
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'username already exists'


def test_create_user_email_integrity_error(
    client: TestClient, user: User
) -> None:
    response = client.post(
        '/users',
        json={
            'username': 'new',
            'email': user.email,
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'email already exists'


def test_update_username_integrity_error(
    client: TestClient, user: User
) -> None:
    client.post(
        '/users',
        json={
            'username': 'vini',
            'email': 'vini@example.com',
            'password': 'secret',
        },
    )

    response = client.put(
        f'/users/{user.id}',
        json={
            'username': 'vini',
            'email': user.email,
            'password': user.password,
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'username or email already exists'


def test_update_email_integrity_error(client: TestClient, user: User) -> None:
    client.post(
        '/users',
        json={
            'username': 'vini',
            'email': 'vini@example.com',
            'password': 'secret',
        },
    )

    response = client.put(
        f'/users/{user.id}',
        json={
            'username': user.username,
            'email': 'vini@example.com',
            'password': user.password,
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'username or email already exists'
