from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..api.routes import router


app = FastAPI(title="Pokémon Card PreGrader API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)
