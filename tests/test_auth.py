from http import HTTPStatus

from fastapi.testclient import TestClient

from fastapi_zero.models import User


def test_get_token(
    client: TestClient, user: User, clean_password: str
) -> None:
    response = client.post(
        '/api/v1/auth/token',
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
        '/api/v1/auth/token',
        data={'username': 'error@example.com', 'password': clean_password},
    )

    error = response.json()

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert error['detail'] == 'Incorrect email or password'


def test_get_token_unauthorized_password(
    client: TestClient, user: User
) -> None:
    response = client.post(
        '/api/v1/auth/token',
        data={'username': user.email, 'password': 'errorPassword'},
    )

    error = response.json()

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert error['detail'] == 'Incorrect email or password'
