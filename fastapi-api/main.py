from fastapi import FastAPI
import routers.auth
import routers.users
import routers.trackers
import routers.activities
import models
from fastapi.middleware.cors import CORSMiddleware
from alembic.config import CommandLine


def create_app():
    app = FastAPI()
    models.init_db()
    app.include_router(routers.auth.router)
    app.include_router(routers.users.router)
    app.include_router(routers.trackers.router)
    app.include_router(routers.activities.router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://traxy-frontend.ue.r.appspot.com",
                       "https://traxy-frontend.uc.r.appspot.com",
                       "https://www.traxy.app",
                       "https://traxy.app"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()
