# ==========================
# 1. IMPORTAÇÕES E TIPAGENS
# ===========================
from collections.abc import AsyncGenerator, Callable, Generator
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from fastapi_zero import security
from fastapi_zero.app import app
from fastapi_zero.database import get_session
from fastapi_zero.models import Todo, User, table_registry
from fastapi_zero.schemas import TodoSchema, UserSchema
from fastapi_zero.security import get_password_hash

type MockDbTime = Callable[
    ..., AbstractContextManager[tuple[datetime, datetime]]
]


# ====================================================================
# 2. INFRAESTRUTURA E BANCO DE DADOS (TestClient, Session, MockTime)
# ====================================================================
@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[TestClient]:
    def get_session_override() -> AsyncSession:
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope='session')
def engine() -> Generator[AsyncEngine]:
    with PostgresContainer('postgres:18', driver='psycopg') as postgres:
        url = postgres.get_connection_url()

        sync_engine = create_engine(url)
        table_registry.metadata.create_all(sync_engine)
        sync_engine.dispose()

        yield create_async_engine(url)


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    async with engine.connect() as conn:
        transaction = await conn.begin()

        async with AsyncSession(
            bind=conn,
            join_transaction_mode='create_savepoint',
            expire_on_commit=False,
        ) as session:
            yield session

        await transaction.rollback()

    await engine.dispose()


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


# ==========================
# 3. AUTENTICAÇÃO E TOKENS
# ==========================
@pytest.fixture
def clean_password() -> str:
    return UserFactory.__faker__.password()


@pytest.fixture(scope='session', autouse=True)
def fast_password_hash() -> Generator[None]:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            security,
            'pwd_context',
            PasswordHash((
                Argon2Hasher(time_cost=1, memory_cost=64, parallelism=1),
            )),
        )
        yield


@pytest.fixture
def token(client: TestClient, user: User, clean_password: str) -> str:
    response = client.post(
        '/api/v1/auth/token',
        data={'username': user.email, 'password': clean_password},
    )

    return response.json()['access_token']


# ==============================
# 4. FÁBRICA User (Polyfactory)
# ==============================
class UserFactory(SQLAlchemyFactory[User]):
    __model__ = User

    @classmethod
    def username(cls) -> str:
        return f'user_{cls.__faker__.unique.user_name()}'

    @classmethod
    def email(cls) -> str:
        return cls.__faker__.unique.email()

    @classmethod
    def password(cls) -> str:
        return get_password_hash(cls.__faker__.password())


# ==============================
# 5. FÁBRICA Todo (Polyfactory)
# ==============================
class TodoFactory(SQLAlchemyFactory[Todo]):
    __model__ = Todo

    @classmethod
    def title(cls) -> str:
        return cls.__faker__.sentence(nb_words=4).rstrip('.')

    @classmethod
    def description(cls) -> str:
        return cls.__faker__.text()


# ==================================================================
# 6. FIXTURES DE Users (Objetos instanciados no banco e Builders)
# ==================================================================
@pytest_asyncio.fixture
async def user(session: AsyncSession, clean_password: str) -> User:
    user = UserFactory.build(password=get_password_hash(clean_password))

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@pytest_asyncio.fixture
async def other_user(session: AsyncSession) -> User:
    user = UserFactory.build()

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


class UserSchemaFactory(ModelFactory[UserSchema]):
    __model__ = UserSchema


# ===============================================================
# 7. FIXTURES DE Todos (Objetos instanciados no banco e Builders)
# ===============================================================
@pytest_asyncio.fixture
async def todo(session: AsyncSession, user: User) -> Todo:
    todo = TodoFactory.build(user_id=user.id)

    session.add(todo)
    await session.commit()
    await session.refresh(todo)

    return todo


class TodoSchemaFactory(ModelFactory[TodoSchema]):
    __model__ = TodoSchema
