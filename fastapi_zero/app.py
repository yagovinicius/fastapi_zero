import asyncio
import sys
from http import HTTPStatus

from fastapi import FastAPI

from fastapi_zero.routes.api import api_router
from fastapi_zero.schemas import Message

if sys.platform == 'win32':  # pragma: no cover
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type: ignore


app = FastAPI(title='APIzinha do Mal')

app.include_router(api_router)


@app.get('/', status_code=HTTPStatus.OK)
async def read_root() -> Message:
    return Message(message='Olá, mundo!')
