from fastapi import FastAPI
from app.routes.github_webhook import router as webhook_router

app = FastAPI()
app.include_router(webhook_router, prefix="/webhook")
