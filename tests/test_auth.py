from http import HTTPStatus

from fastapi.testclient import TestClient
from freezegun.api import freeze_time

from fastapi_zero.models import User
from tests.conftest import UserSchemaFactory


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


def test_token_expired_after_time(
    client: TestClient,
    user: User,
    clean_password: str,
) -> None:
    changes = UserSchemaFactory.build()
    with freeze_time('2026-10-10 17:00:00'):
        response = client.post(
            '/api/v1/auth/token',
            data={'username': user.email, 'password': clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']

    with freeze_time('2026-10-10 17:31:00'):
        response = client.put(
            f'/api/v1/users/{user.id}',
            headers={'Authorization': f'Bearer {token}'},
            json=changes.model_dump(mode='json'),
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json()['detail'] == 'Could not validate credentials'


def test_refresh_token(client: TestClient, token: str) -> None:
    response = client.post(
        '/api/v1/auth/refresh_token',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in response.json()
    assert 'token_type' in response.json()
    assert response.json()['token_type'] == 'Bearer'


def test_refresh_token_user_unauthorized(client: TestClient) -> None:
    response = client.post(
        '/api/v1/auth/refresh_token',
        headers={'Authorization': 'Bearer invalid-token'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Could not validate credentials'


def test_token_expired_dont_refresh(
    client: TestClient,
    user: User,
    clean_password: str,
) -> None:
    with freeze_time('2026-10-10 17:00:00'):
        response = client.post(
            '/api/v1/auth/token',
            data={'username': user.email, 'password': clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']

    with freeze_time('2026-10-10 17:31:00'):
        response = client.post(
            '/api/v1/auth/refresh_token',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json()['detail'] == 'Could not validate credentials'
