from fastapi import APIRouter
from .auth import router as auth_router
from .chat import router as chat_router
from .users import router as users_router
from .prompt_check import router as prompt_check_router
from .visualization import router as visualization_router
from .tokens import router as tokens_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(
    prompt_check_router, prefix="/prompt-check", tags=["prompt-check"]
)
api_router.include_router(
    visualization_router, prefix="/visualization", tags=["visualization"]
)
api_router.include_router(tokens_router, prefix="/tokens", tags=["tokens"])
