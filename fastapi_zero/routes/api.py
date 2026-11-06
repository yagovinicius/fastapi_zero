from fastapi import APIRouter

from fastapi_zero.routes import (
    auth,
    users,
)

api_router = APIRouter(prefix='/api/v1')

api_router.include_router(auth.router)
api_router.include_router(users.router)
