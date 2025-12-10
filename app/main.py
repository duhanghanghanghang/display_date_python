import asyncio
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from .routers import auth, items, teams, notify
from .notifier import notifier_loop

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Display Date API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(items.router)
app.include_router(teams.router)
app.include_router(notify.router)


@app.get("/", response_class=PlainTextResponse)
def read_root() -> str:
    return "番茄我爱你"


@app.on_event("startup")
async def _start_notifier():
    asyncio.create_task(notifier_loop())

