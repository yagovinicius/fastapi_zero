from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.schemas import (
    Message,
    UserList,
    UserPublic,
    UserSchema,
)

app = FastAPI(title='APIzinha do Mal')


@app.get('/', status_code=HTTPStatus.OK)
def read_root() -> Message:
    return Message(message='Olá, mundo!')


@app.post('/users', status_code=HTTPStatus.CREATED)
def create_user(
    user: UserSchema, session: Session = Depends(get_session)
) -> UserPublic:

    db_user = session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )

    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='username already exists',
            )
        else:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail='email already exists'
            )

    db_user = User(**user.model_dump())

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return UserPublic.model_validate(db_user)


@app.get('/users', status_code=HTTPStatus.OK)
def get_users(
    limit: int = 10, offset: int = 0, session: Session = Depends(get_session)
) -> UserList:

    return UserList.model_validate({
        'users': session.scalars(
            select(User).limit(limit).offset(offset)
        ).all()
    })


@app.get('/users/{user_id}', status_code=HTTPStatus.OK)
def get_user_by_id(
    user_id: int, session: Session = Depends(get_session)
) -> UserPublic:
    user_db = session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='user not found'
        )

    return UserPublic.model_validate(user_db)


@app.put('/users/{user_id}', status_code=HTTPStatus.OK)
def update_user(
    user_id: int, user: UserSchema, session: Session = Depends(get_session)
) -> UserPublic:
    user_db = session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='user not found'
        )

    try:
        user_db.username = user.username
        user_db.email = user.email
        user_db.password = user.password

        session.commit()
        session.refresh(user_db)

        return UserPublic.model_validate(user_db)

    except IntegrityError as e:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='username or email already exists',
        ) from e


@app.delete('/users/{user_id}', status_code=HTTPStatus.OK)
def delete_user(
    user_id: int, session: Session = Depends(get_session)
) -> Message:
    user_db = session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='user not found'
        )

    session.delete(user_db)
    session.commit()

    return Message(message='user has been deleted')
