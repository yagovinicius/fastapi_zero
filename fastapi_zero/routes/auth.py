from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_zero.database import get_session
from fastapi_zero.models import User
from fastapi_zero.schemas import Token
from fastapi_zero.security import (
    create_access_token,
    verify_password,
)

router = APIRouter(prefix='/auth', tags=['auth'])

type OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]
type SessionDep = Annotated[Session, Depends(get_session)]


@router.post('/token')
def login_for_access_token(
    form_data: OAuth2Form,
    session: SessionDep,
) -> Token:
    user = session.scalar(select(User).where(User.email == form_data.username))

    if not user:
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED, detail='Incorrect email or password'
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED, detail='Incorrect email or password'
        )

    access_token = create_access_token({'sub': user.email})

    return Token(access_token=access_token, token_type='Bearer')
