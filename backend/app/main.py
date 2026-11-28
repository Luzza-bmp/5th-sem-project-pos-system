from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.stores import router as stores_router
from app.config import settings

if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
    raise RuntimeError("Set JWT_SECRET_KEY in backend/.env (at least 32 random characters)")

app = FastAPI(title="Pasaley POS API", version="1.0.0")
app.include_router(auth_router)
app.include_router(stores_router)


@app.get("/health")
def health():
    return {"status": "ok"}
