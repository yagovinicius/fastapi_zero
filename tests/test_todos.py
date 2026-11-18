from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_zero.models import Todo, TodoState, User
from fastapi_zero.schemas import TodoPublic
from tests.conftest import MockDbTime, TodoFactory, TodoSchemaFactory


def test_create_todo(
    client: TestClient,
    user: User,
    token: str,
    mock_db_time: MockDbTime,
) -> None:
    with mock_db_time(model=Todo) as (time_post, _time_put):
        todo_schema = TodoSchemaFactory.build()
        response = client.post(
            '/api/v1/todos',
            headers={'Authorization': f'Bearer {token}'},
            json=todo_schema.model_dump(mode='json'),
        )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'title': todo_schema.title,
        'description': todo_schema.description,
        'state': todo_schema.state.value,
        'id': 1,
        'created_at': time_post.isoformat(),
        'updated_at': time_post.isoformat(),
    }


@pytest.mark.asyncio
async def test_list_todos_should_return_5_todos(
    client: TestClient,
    session: AsyncSession,
    user: User,
    token: str,
) -> None:
    # arrange
    expected_todos = 5
    session.add_all(TodoFactory.batch(5, user_id=user.id))
    await session.commit()

    # act
    response = client.get(
        '/api/v1/todos',
        headers={'Authorization': f'Bearer {token}'},
    )

    # assert
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_pagination_should_return_2_todos(
    client: TestClient,
    session: AsyncSession,
    user: User,
    token: str,
) -> None:
    # arrange
    expected_todos = 2
    session.add_all(TodoFactory.batch(5, user_id=user.id))
    await session.commit()

    # act
    response = client.get(
        '/api/v1/todos',
        headers={'Authorization': f'Bearer {token}'},
        params={
            'offset': 1,
            'limit': 2,
        },
    )

    # assert
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_title_should_return_5_todos(
    client: TestClient,
    session: AsyncSession,
    user: User,
    token: str,
) -> None:
    # arrange
    expected_todos = 5

    session.add_all(TodoFactory.batch(5, user_id=user.id, title='Test todo 1'))

    session.add_all(TodoFactory.batch(5, user_id=user.id))

    await session.commit()

    # act
    response = client.get(
        '/api/v1/todos',
        headers={'Authorization': f'Bearer {token}'},
        params={
            'title': 'Test todo 1',
        },
    )

    # assert
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_description_should_return_5_todos(
    client: TestClient,
    session: AsyncSession,
    user: User,
    token: str,
) -> None:
    # arrange
    expected_todos = 5
    session.add_all(
        TodoFactory.batch(5, user_id=user.id, description='description')
    )

    session.add_all(TodoFactory.batch(5, user_id=user.id))

    await session.commit()

    # act
    response = client.get(
        '/api/v1/todos',
        headers={'Authorization': f'Bearer {token}'},
        params={
            'description': 'description',
        },
    )

    # assert
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_state_should_return_5_todos(
    client: TestClient,
    session: AsyncSession,
    user: User,
    token: str,
) -> None:
    # arrange
    expected_todos = 5

    session.add_all(
        TodoFactory.batch(5, user_id=user.id, state=TodoState.draft)
    )

    session.add_all(
        TodoFactory.batch(5, user_id=user.id, state=TodoState.todo)
    )

    await session.commit()

    # act
    response = client.get(
        '/api/v1/todos',
        headers={'Authorization': f'Bearer {token}'},
        params={
            'state': TodoState.draft,
        },
    )

    # assert
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_combined_should_return_5_todos(
    session: AsyncSession,
    user: User,
    client: TestClient,
    token: str,
) -> None:
    expected_todos = 5
    session.add_all(
        TodoFactory.batch(
            5,
            user_id=user.id,
            title='Test todo combined',
            description='combined description',
            state=TodoState.done,
        )
    )

    session.add_all(
        TodoFactory.batch(
            3,
            user_id=user.id,
            title='Other title',
            description='other description',
            state=TodoState.todo,
        )
    )
    await session.commit()

    response = client.get(
        '/api/v1/todos',
        headers={'Authorization': f'Bearer {token}'},
        params={
            'title': 'Test todo combined',
            'description': 'combined description',
            'state': TodoState.done,
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['todos']) == expected_todos


def test_delete_todo(
    client: TestClient,
    token: str,
    todo: Todo,
) -> None:
    response = client.delete(
        f'/api/v1/todos/{todo.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['message'] == 'Task has been deleted successfully.'


@pytest.mark.asyncio
async def test_delete_other_user_todo(
    session: AsyncSession,
    client: TestClient,
    token: str,
    other_user: User,
) -> None:
    # arrange
    todo_other_user = TodoFactory.build(user_id=other_user.id)

    session.add(todo_other_user)
    await session.commit()

    response = client.delete(
        f'/api/v1/todos/{todo_other_user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Task not found.'


def test_delete_todo_error(
    client: TestClient,
    token: str,
) -> None:
    response = client.delete(
        '/api/v1/todos/10', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Task not found.'


def test_patch_todo(
    client: TestClient,
    token: str,
    todo: Todo,
    mock_db_time: MockDbTime,
) -> None:
    with mock_db_time(model=Todo) as (_time_post, time_put):
        response = client.patch(
            f'/api/v1/todos/{todo.id}',
            json={'title': 'test!'},
            headers={'Authorization': f'Bearer {token}'},
        )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'title': 'test!',
        'description': todo.description,
        'state': todo.state.value,
        'id': todo.id,
        'created_at': todo.created_at.isoformat(),
        'updated_at': time_put.isoformat(),
    }


def test_patch_todo_error(client: TestClient, token: str) -> None:
    response = client.patch(
        '/api/v1/todos/10',
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Task not found.'


@pytest.mark.asyncio
async def test_list_todos_should_return_all_expected_fields(
    client: TestClient, user: User, token: str, session: AsyncSession
) -> None:
    # arrange
    todo = TodoFactory.build(user_id=user.id)
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    expected_todo = TodoPublic.model_validate(todo).model_dump(mode='json')

    # act
    response = client.get(
        '/api/v1/todos',
        headers={'Authorization': f'Bearer {token}'},
    )

    # assert
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'todos': [expected_todo]}


@pytest.mark.asyncio
async def test_create_todo_error(session: AsyncSession) -> None:
    todo_error = TodoFactory.build(state='invalid')

    session.add(todo_error)
    await session.commit()

    with pytest.raises(LookupError):
        await session.refresh(todo_error)


def test_list_todos_filter_min_length(client: TestClient, token: str) -> None:
    response = client.get(
        '/api/v1/todos',
        headers={'Authorization': f'Bearer {token}'},
        params={'title': 'ab'},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT

    detail = response.json()['detail'][0]
    assert detail['type'] == 'string_too_short'
    assert detail['loc'] == ['query', 'title']
    assert detail['msg'] == 'String should have at least 3 characters'
    assert detail['ctx'] == {'min_length': 3}


def test_list_todos_filter_max_length(client: TestClient, token: str) -> None:
    response = client.get(
        '/api/v1/todos',
        headers={'Authorization': f'Bearer {token}'},
        params={'title': 'more_than_twenty_characters'},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT

    detail = response.json()['detail'][0]
    assert detail['type'] == 'string_too_long'
    assert detail['loc'] == ['query', 'title']
    assert detail['msg'] == 'String should have at most 20 characters'
    assert detail['ctx'] == {'max_length': 20}
