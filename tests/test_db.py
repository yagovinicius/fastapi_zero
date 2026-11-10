from dataclasses import asdict

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_zero.database import get_session
from fastapi_zero.models import User
from tests.conftest import MockDbTime


@pytest.mark.asyncio
async def test_create_user(
    session: AsyncSession, mock_db_time: MockDbTime
) -> None:
    with mock_db_time(model=User) as (time_post, _time_put):
        new_user = User(
            username='test',
            email='test@example.com',
            password='secret',
        )

        session.add(new_user)
        await session.commit()

        user = await session.scalar(
            select(User).where(User.username == 'test')
        )

    assert user is not None
    assert asdict(user) == {
        'id': 1,
        'username': 'test',
        'email': 'test@example.com',
        'password': 'secret',
        'created_at': time_post,
        'updated_at': time_post,
    }


@pytest.mark.asyncio
async def test_update_user(
    session: AsyncSession, mock_db_time: MockDbTime
) -> None:
    with mock_db_time(model=User) as (time_post, time_put):
        new_user = User(
            username='test',
            email='test@example.com',
            password='secret',
        )

        session.add(new_user)
        await session.commit()

        user = await session.scalar(
            select(User).where(User.username == 'test')
        )

        assert user is not None

        user.username = 'test2'
        user.email = 'test2@example.com'
        user.password = 'secret2'

        await session.commit()
        await session.refresh(user)

        assert asdict(user) == {
            'id': 1,
            'username': 'test2',
            'email': 'test2@example.com',
            'password': 'secret2',
            'created_at': time_post,
            'updated_at': time_put,
        }


@pytest.mark.asyncio
async def test_get_session() -> None:
    session = await anext(get_session())

    response: int | None = await session.scalar(select(1))
    assert response == 1
