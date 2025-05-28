from fastapi import FastAPI
import routers.auth, routers.users, routers.trackers, routers.activities, models
from fastapi.middleware.cors import CORSMiddleware
def create_app():
    app = FastAPI()
    models.init_db()
    app.include_router(routers.auth.router)
    app.include_router(routers.users.router)
    app.include_router(routers.trackers.router)
    app.include_router(routers.activities.router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://traxy-frontend.ue.r.appspot.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app

app = create_app()
