import secrets
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from fastapi_zero.app import app
from fastapi_zero.database import get_session
from fastapi_zero.models import User, table_registry
from fastapi_zero.security import get_password_hash

type MockDbTime = Callable[
    ..., AbstractContextManager[tuple[datetime, datetime]]
]


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[TestClient]:
    def get_session_override() -> AsyncSession:
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    # cria a engine
    engine = create_async_engine(
        'sqlite+aiosqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)


@contextmanager
def _mock_db_time(
    *,
    model: type[Any],
    time_post: datetime = datetime(2026, 10, 10),
    time_put: datetime = datetime(2026, 10, 12),
) -> Generator[tuple[datetime, datetime]]:

    def fake_insert_hook(
        _mapper: object, _connection: object, target: Any
    ) -> None:
        if hasattr(target, 'created_at'):
            target.created_at = time_post
        if hasattr(target, 'updated_at'):
            target.updated_at = time_post

    def fake_update_hook(
        _mapper: object, _connection: object, target: Any
    ) -> None:
        if hasattr(target, 'updated_at'):
            target.updated_at = time_put

    event.listen(model, 'before_insert', fake_insert_hook)
    event.listen(model, 'before_update', fake_update_hook)

    yield time_post, time_put

    event.remove(model, 'before_insert', fake_insert_hook)
    event.remove(model, 'before_update', fake_update_hook)


@pytest.fixture
def mock_db_time() -> MockDbTime:
    return _mock_db_time


@pytest.fixture
def clean_password() -> str:
    return secrets.token_hex()


@pytest_asyncio.fixture
async def user(session: AsyncSession, clean_password: str) -> User:
    user = User(
        username='test',
        email='test@example.com',
        password=get_password_hash(clean_password),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@pytest.fixture
def token(client: TestClient, user: User, clean_password: str) -> str:
    response = client.post(
        '/api/v1/auth/token',
        data={'username': user.email, 'password': clean_password},
    )

    return response.json()['access_token']
