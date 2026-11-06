import secrets
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
            'password': secrets.token_hex(),
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'username': 'alice',
        'email': 'alice@example.com',
    }


def test_get_users(client: TestClient, user: User, token: str) -> None:
    user_schema = UserPublic.model_validate(user).model_dump(mode='json')

    response = client.get(
        '/users',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )

    assert response.json() == {'users': [user_schema]}


def test_get_user_by_id(client: TestClient, user: User) -> None:
    user_schema = UserPublic.model_validate(user).model_dump(mode='json')

    response = client.get(f'/users/{user.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == user_schema


def test_get_user_by_id_not_found(client: TestClient, user: User) -> None:
    response = client.get(f'/users/{user.id + 1}')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'User not found'


def test_update_user(client: TestClient, token: str) -> None:
    response = client.put(
        '/users/1',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': secrets.token_hex(),
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': 1,
        'username': 'bob',
        'email': 'bob@example.com',
    }


def test_delete_user(client: TestClient, token: str) -> None:
    response = client.delete(
        '/users/1',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['message'] == 'user has been deleted'


def test_update_user_forbidden(
    client: TestClient, user: User, token: str
) -> None:
    response = client.put(
        f'/users/{user.id + 1}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json={
            'username': 'test',
            'email': 'test@example.com',
            'password': secrets.token_hex(),
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_delete_user_forbidden(
    client: TestClient, user: User, token: str
) -> None:
    response = client.delete(
        f'/users/{user.id + 1}',
        headers={
            'Authorization': f'Bearer {token}',
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_create_user_username_integrity_error(
    client: TestClient, user: User
) -> None:
    response = client.post(
        '/users',
        json={
            'username': user.username,
            'email': 'new@example.com',
            'password': secrets.token_hex(),
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Username already exists'


def test_create_user_email_integrity_error(
    client: TestClient, user: User
) -> None:
    response = client.post(
        '/users',
        json={
            'username': 'new',
            'email': user.email,
            'password': secrets.token_hex(),
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Email already exists'


def test_update_username_integrity_error(
    client: TestClient, user: User, token: str
) -> None:
    # Criando usuário
    client.post(
        '/users',
        json={
            'username': 'vini',
            'email': 'vini@example.com',
            'password': secrets.token_hex(),
        },
    )

    # Tentando usar o nome do usuário criado em outro
    response = client.put(
        f'/users/{user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json={
            'username': 'vini',
            'email': user.email,
            'password': user.password,
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Username or email already exists'


def test_update_email_integrity_error(
    client: TestClient, user: User, token: str
) -> None:
    # Criando usuário
    client.post(
        '/users',
        json={
            'username': 'vini',
            'email': 'vini@example.com',
            'password': secrets.token_hex(),
        },
    )

    # Tentando usar o nome do usuário criado em outro
    response = client.put(
        f'/users/{user.id}',
        headers={
            'Authorization': f'Bearer {token}',
        },
        json={
            'username': user.username,
            'email': 'vini@example.com',
            'password': user.password,
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Username or email already exists'


# def test_get_users_unauthorized(client: TestClient):
#     response = client.get('/users')

#     assert response.status_code == HTTPStatus.UNAUTHORIZED
#     assert response.json()['detail'] == 'Not authenticated'
