from datetime import datetime, timezone

from fastapi import FastAPI

from app.api.nodes import router as nodes_router
from app.core.config import settings
from app.db.session import Base, engine
from app.models import Node  # noqa: F401


Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "time": datetime.now(timezone.utc).isoformat(),
    }


app.include_router(nodes_router)
