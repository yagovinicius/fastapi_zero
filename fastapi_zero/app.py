from http import HTTPStatus

from fastapi import FastAPI

from fastapi_zero.routes.api import api_router
from fastapi_zero.schemas import Message

app = FastAPI(title='APIzinha do Mal')

app.include_router(api_router)


@app.get('/', status_code=HTTPStatus.OK)
def read_root() -> Message:
    return Message(message='Olá, mundo!')
