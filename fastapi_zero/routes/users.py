from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.schemas import (
    FilterPage,
    Message,
    UserList,
    UserPublic,
    UserSchema,
)
from fastapi_zero.security import get_current_user, get_password_hash

router = APIRouter(prefix='/users', tags=['users'])

type SessionDep = Annotated[Session, Depends(get_session)]
type CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post('/', status_code=HTTPStatus.CREATED)
def create_user(
    user: UserSchema,
    session: SessionDep,
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
                detail='Username already exists',
            )
        else:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail='Email already exists'
            )

    user.password = get_password_hash(user.password)
    db_user = User(**user.model_dump())

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return UserPublic.model_validate(db_user)


@router.get('/', status_code=HTTPStatus.OK)
def get_users(
    session: SessionDep,
    current_user: CurrentUser,
    filter_users: Annotated[FilterPage, Query()],
) -> UserList:

    return UserList.model_validate({
        'users': session.scalars(
            select(User).limit(filter_users.limit).offset(filter_users.offset)
        ).all()
    })


@router.get('/{user_id}', status_code=HTTPStatus.OK)
def get_user_by_id(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> UserPublic:
    user_db = session.scalar(select(User).where(User.id == user_id))

    if not user_db:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    return UserPublic.model_validate(user_db)


@router.put('/{user_id}', status_code=HTTPStatus.OK)
def update_user(
    user_id: int,
    user: UserSchema,
    session: SessionDep,
    current_user: CurrentUser,
) -> UserPublic:

    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permission'
        )

    try:
        current_user.username = user.username
        current_user.email = user.email
        current_user.password = get_password_hash(user.password)

        session.commit()
        session.refresh(current_user)

        return UserPublic.model_validate(current_user)

    except IntegrityError as e:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Username or email already exists',
        ) from e


@router.delete('/{user_id}', status_code=HTTPStatus.OK)
def delete_user(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Message:

    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permission'
        )

    session.delete(current_user)
    session.commit()

    return Message(message='user has been deleted')
