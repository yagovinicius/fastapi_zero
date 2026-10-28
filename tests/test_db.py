from dataclasses import asdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_zero.models import User


def test_create_user(session: Session, mock_db_time: Any) -> None:
    with mock_db_time(model=User) as (time_post, _time_put):
        new_user = User(
            username='test',
            email='test@example.com',
            password='secret',
        )

        session.add(new_user)
        session.commit()

        user = session.scalar(select(User).where(User.username == 'test'))

    assert user is not None
    assert asdict(user) == {
        'id': 1,
        'username': 'test',
        'email': 'test@example.com',
        'password': 'secret',
        'created_at': time_post,
        'updated_at': time_post,
    }


def test_update_user(session: Session, mock_db_time: Any) -> None:
    with mock_db_time(model=User) as (time_post, time_put):
        new_user = User(
            username='test',
            email='test@example.com',
            password='secret',
        )

        session.add(new_user)
        session.commit()

        user = session.scalar(select(User).where(User.username == 'test'))

        assert user is not None

        user.username = 'test2'
        user.email = 'test2@example.com'
        user.password = 'secret2'

        session.commit()
        session.refresh(user)

        assert asdict(user) == {
            'id': 1,
            'username': 'test2',
            'email': 'test2@example.com',
            'password': 'secret2',
            'created_at': time_post,
            'updated_at': time_put,
        }
