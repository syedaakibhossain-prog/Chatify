from fastapi import FastAPI
from src.authentication.routes import router as auth_router
from src.chat.ConversessionRoutes import router as conversession_router
from src.chat.MessageRoutes import router as message_router
from src.websockets.routes import router as ws_router
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from src.database import engine, BaseModel


from src.model import User, Conversession, Member, Message


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
    allow_origins="http://127.0.0.1:5500/test/test.html",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(conversession_router)
app.include_router(message_router)
app.include_router(ws_router)



@app.get("/")
def root():
    return {"status" : "ok"}