from fastapi import APIRouter

from app.routes.batch import router as batch_router
from app.routes.cases import router as cases_router
from app.routes.clock import router as clock_router
from app.routes.chat import router as chat_router
from app.routes.escalation import router as escalation_router
from app.routes.webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(batch_router)
api_router.include_router(cases_router)
api_router.include_router(clock_router)
api_router.include_router(chat_router)
api_router.include_router(escalation_router)
api_router.include_router(webhooks_router)

__all__ = ["api_router"]
