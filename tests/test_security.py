from http import HTTPStatus

from fastapi.testclient import TestClient
from jwt import decode

from fastapi_zero.security import create_access_token, settings


def test_jwt() -> None:
    data = {'test': 'test'}

    token = create_access_token(data)

    decoded = decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)

    assert decoded['test'] == data['test']
    assert 'exp' in decoded


# Decode exception
def test_jwt_invalid_token(client: TestClient) -> None:
    response = client.delete(
        '/api/v1/users/1', headers={'Authorization': 'Bearer invalid-token'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


# Subject email exception
def test_get_current_not_found(client: TestClient) -> None:
    data = {'no-email': 'test'}
    token = create_access_token(data)

    response = client.delete(
        '/api/v1/users/1', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


# Subject email exception 2
def test_get_current_user_does_not_exists(client: TestClient) -> None:
    data = {'sub': 'test@test'}
    token = create_access_token(data)

    response = client.delete(
        '/api/v1/users/1', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}
