from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.db.session import engine, Base
from app.routes.batches import router as batches_router

def create_app() -> FastAPI:
    app = FastAPI(title="DocGen API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup():
        # Create tables (dev convenience). In production, use migrations.
        Base.metadata.create_all(bind=engine)

    app.include_router(batches_router)
    return app

app = create_app()
