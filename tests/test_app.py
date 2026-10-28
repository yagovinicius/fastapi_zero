from http import HTTPStatus

from fastapi.testclient import TestClient


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
    assert response.json()['username'] == 'alice'
    assert response.json()['email'] == 'alice@example.com'
    assert response.json()['id'] == 1

    assert 'created_at' in response.json()
    assert 'updated_at' in response.json()


def test_read_users(client: TestClient) -> None:
    response = client.get('/users')
    assert response.status_code == HTTPStatus.OK

    assert response.json()['users'][0]['username'] == 'alice'
    assert response.json()['users'][0]['email'] == 'alice@example.com'
    assert response.json()['users'][0]['id'] == 1

    assert 'created_at' in response.json()['users'][0]
    assert 'updated_at' in response.json()['users'][0]


def test_get_user_by_id(client: TestClient) -> None:
    response = client.get('/users/1')

    assert response.status_code == HTTPStatus.OK

    assert response.json()['username'] == 'alice'
    assert response.json()['email'] == 'alice@example.com'
    assert response.json()['id'] == 1

    assert 'created_at' in response.json()
    assert 'updated_at' in response.json()


def test_update_user(client: TestClient) -> None:
    response = client.put(
        '/users/1',
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['username'] == 'bob'
    assert response.json()['email'] == 'bob@example.com'
    assert response.json()['id'] == 1

    assert 'created_at' in response.json()
    assert 'updated_at' in response.json()


def test_delete_user(client: TestClient) -> None:
    response = client.delete('/users/1')
    assert response.status_code == HTTPStatus.NO_CONTENT


def test_get_user_by_id_not_found(client: TestClient) -> None:
    response = client.get('/users/1')
    assert response.status_code == HTTPStatus.NOT_FOUND


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
