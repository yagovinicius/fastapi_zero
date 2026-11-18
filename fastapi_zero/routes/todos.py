from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_zero.database import get_session
from fastapi_zero.models import Todo, User
from fastapi_zero.schemas import (
    FilterTodo,
    Message,
    TodoList,
    TodoPublic,
    TodoSchema,
    TodoUpdate,
)
from fastapi_zero.security import get_current_user

router = APIRouter(prefix='/todos', tags=['todos'])

type SessionDep = Annotated[AsyncSession, Depends(get_session)]
type CurrentUser = Annotated[User, Depends(get_current_user)]
type FilterDep = Annotated[FilterTodo, Query()]


@router.post('/', status_code=HTTPStatus.OK)
async def create_todo(
    session: SessionDep, user: CurrentUser, todo: TodoSchema
) -> TodoPublic:
    todo_model = Todo(**todo.model_dump(), user_id=user.id)

    session.add(todo_model)
    await session.commit()
    await session.refresh(todo_model)

    return TodoPublic.model_validate(todo_model)


@router.get('/', status_code=HTTPStatus.OK)
async def list_todos(
    user: CurrentUser,
    session: SessionDep,
    todo_filter: FilterDep,
) -> TodoList:
    query = select(Todo).where(Todo.user_id == user.id)

    filters = todo_filter.model_dump(
        exclude={'offset', 'limit'},
        exclude_none=True,
    )

    for key, value in filters.items():
        col = getattr(Todo, key)

        if key == 'state':
            query = query.filter(col == value)
        else:
            query = query.filter(col.contains(value))

    todos = await session.scalars(
        query.limit(todo_filter.limit).offset(todo_filter.offset)
    )

    return TodoList.model_validate({'todos': todos.all()})


@router.delete('/{todo_id}', status_code=HTTPStatus.OK)
async def delete_todo(
    todo_id: int,
    session: SessionDep,
    user: CurrentUser,
) -> Message:
    db_todo = await session.scalar(
        select(Todo).where(Todo.user_id == user.id, Todo.id == todo_id)
    )

    if not db_todo:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            detail='Task not found.',
        )

    await session.delete(db_todo)
    await session.commit()

    return Message(message='Task has been deleted successfully.')


@router.patch('/{todo_id}', status_code=HTTPStatus.OK)
async def patch_todo(
    todo_id: int,
    session: SessionDep,
    user: CurrentUser,
    todo: TodoUpdate,
) -> TodoPublic:
    db_todo = await session.scalar(
        select(Todo).where(Todo.user_id == user.id, Todo.id == todo_id)
    )

    if not db_todo:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Task not found.'
        )

    for key, value in todo.model_dump(exclude_unset=True).items():
        setattr(db_todo, key, value)

    await session.commit()
    await session.refresh(db_todo)

    return TodoPublic.model_validate(db_todo)
