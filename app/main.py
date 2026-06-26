from fastapi import FastAPI
from app.db.database import engine
from app.db import models

# Import your new router!
from app.api import routes

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Buguard Asset Management API",
    description="Track B: Minimal API and AI Analysis Layer",
    version="1.0.0"
)

# Tell the app to use the routes you just created
app.include_router(routes.router, prefix="/api/v1", tags=["Assets"])

@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "Welcome to the DarkAtlas Asset Management API. The database is connected!"
    }
