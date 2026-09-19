from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.authentication.routes import router as auth_router
from src.converseation.router import router as conversation_router
from src.database import BaseModel, engine
from src.message.router import router as message_router
from src.user.router import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(
            BaseModel.metadata.create_all
        )

    yield


app = FastAPI(
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(conversation_router)
app.include_router(message_router)


@app.get("/")
def root():
    return {"status" : "ok"}
