from http import HTTPStatus

from fastapi.testclient import TestClient
from jwt import decode

from fastapi_zero.models import User
from fastapi_zero.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
)


def test_jwt() -> None:
    data = {'test': 'test'}

    token = create_access_token(data)

    decoded = decode(token, SECRET_KEY, algorithms=ALGORITHM)

    assert decoded['test'] == data['test']
    assert 'exp' in decoded


def test_get_token(
    client: TestClient, user: User, clean_password: str
) -> None:
    response = client.post(
        '/token',
        data={
            'username': user.email,
            'password': clean_password,
        },
    )

    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert token['token_type'] == 'Bearer'
    assert 'access_token' in token


def test_get_token_unauthorized_email(
    client: TestClient, clean_password: str
) -> None:
    response = client.post(
        '/token',
        data={'username': 'error@example.com', 'password': clean_password},
    )

    error = response.json()

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert error['detail'] == 'Incorrect email or password'


def test_get_token_unauthorized_password(
    client: TestClient, user: User
) -> None:
    response = client.post(
        '/token',
        data={'username': user.email, 'password': 'errorPassword'},
    )

    error = response.json()

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert error['detail'] == 'Incorrect email or password'


# Decode exception
def test_jwt_invalid_token(client: TestClient) -> None:
    response = client.delete(
        '/users/1', headers={'Authorization': 'Bearer invalid-token'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


# Subject email exception
def test_get_current_not_found(client: TestClient) -> None:
    data = {'no-email': 'test'}
    token = create_access_token(data)

    response = client.delete(
        '/users/1', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


# Subject email exception 2
def test_get_current_user_does_not_exists(client: TestClient) -> None:
    data = {'sub': 'test@test'}
    token = create_access_token(data)

    response = client.delete(
        '/users/1', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}
