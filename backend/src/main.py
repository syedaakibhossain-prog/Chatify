import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.authentication.routes import router as auth_router
from src.converseation.router import router as conversation_router
from src.database import BaseModel, engine
from src.message.router import router as message_router
from src.realtime.router import router as realtime_router
from src.redis.redisClient import RedisClient
from src.user.router import router as user_router
from src.config import settings

logger = logging.getLogger("chatify")


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(
            BaseModel.metadata.create_all
        )
    try:
        await RedisClient.get().ping()
        logger.info("startup.redis.connected")
    except Exception as e:
        logger.error("startup.redis.unavailable error=%s", e)
        raise

    yield

    await RedisClient.close()




app = FastAPI(
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"(http|https)://(localhost|127\.0\.0\.1|10\.0\.2\.2)(:\d+)?|exp://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(conversation_router)
app.include_router(message_router)
app.include_router(realtime_router)

@app.get("/")
def root():
    return {"status" : "ok"}
