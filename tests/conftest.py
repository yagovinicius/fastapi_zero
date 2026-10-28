from contextlib import contextmanager
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from fastapi_zero.app import app
from fastapi_zero.models import table_registry


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def session():  # type: ignore
    # cria a engine
    engine = create_engine('sqlite://')

    # cria as tabelas na engine
    table_registry.metadata.create_all(engine)

    # abre a sessão na engine
    with Session(engine) as session:
        yield session

    # limpa a engine ao terminar a execução
    table_registry.metadata.drop_all(engine)


@contextmanager
def _mock_db_time(
    *,
    model: type[Any],
    time_post: datetime = datetime(2026, 10, 10),
    time_put: datetime = datetime(2026, 10, 12),
):
    def fake_insert_hook(_mapper: Any, _connection: Any, target: Any) -> None:
        if hasattr(target, 'created_at'):
            target.created_at = time_post
        if hasattr(target, 'updated_at'):
            target.updated_at = time_post

    def fake_update_hook(_mapper: Any, _connection: Any, target: Any) -> None:
        if hasattr(target, 'updated_at'):
            target.updated_at = time_put

    event.listen(model, 'before_insert', fake_insert_hook)
    event.listen(model, 'before_update', fake_update_hook)

    yield time_post, time_put

    event.remove(model, 'before_insert', fake_insert_hook)
    event.remove(model, 'before_update', fake_update_hook)


@pytest.fixture
def mock_db_time() -> Any:
    return _mock_db_time
