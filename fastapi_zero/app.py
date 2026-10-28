from http import HTTPStatus

from fastapi import FastAPI, HTTPException

from fastapi_zero.schemas import (
    Message,
    UserDB,
    UserList,
    UserPublic,
    UserSchema,
)

app = FastAPI(title='APIzinha do Mal')
database: list[UserDB] = []


@app.get('/', status_code=HTTPStatus.OK)
def read_root() -> Message:
    return Message(message='Olá, mundo!')


@app.post('/users', status_code=HTTPStatus.CREATED)
def create_user(user: UserSchema) -> UserPublic:
    user_with_id = UserDB(**user.model_dump(), id=len(database) + 1)

    database.append(user_with_id)

    return UserPublic.model_validate(user_with_id)


@app.get('/users', status_code=HTTPStatus.OK)
def get_user() -> UserList:

    public_users = [UserPublic.model_validate(user) for user in database]

    return UserList(users=public_users)


@app.get('/users/{id}', status_code=HTTPStatus.OK)
def get_user_by_id(id: int) -> UserPublic:
    if id < 1 or id > len(database):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='User not found.',
        )

    user_by_id = next(user for user in database if user.id == id)

    return UserPublic.model_validate(user_by_id)


@app.put('/users/{user_id}', status_code=HTTPStatus.OK)
def update_user(user_id: int, user: UserSchema) -> UserPublic:
    if user_id < 1 or user_id > len(database):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='User not found.',
        )

    user_with_id = UserDB(**user.model_dump(), id=user_id)

    database[user_id - 1] = user_with_id

    return UserPublic.model_validate(user_with_id)


@app.delete('/users/{user_id}', status_code=HTTPStatus.NO_CONTENT)
def delete_user(user_id: int) -> None:
    if user_id < 1 or user_id > len(database):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='User not found.',
        )

    database.pop(user_id - 1)
