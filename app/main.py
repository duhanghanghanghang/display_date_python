import asyncio
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
from .database import Base, engine, SessionLocal
from .routers import auth, items, teams, notify, webhook, upload, barcode, wardrobe
from .notifier import notifier_loop
from .logger import logger, log_manager
from .middleware import LoggingMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Display Date API", version="0.1.0")

# 添加日志中间件（必须在CORS之后）
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（用于图片访问）
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(items.router)
app.include_router(teams.router)
app.include_router(notify.router)
app.include_router(webhook.router)
app.include_router(upload.router)
app.include_router(barcode.router)
app.include_router(wardrobe.router)


@app.get("/", response_class=PlainTextResponse)
def read_root() -> str:
    return """番茄我爱你

备案信息：渝ICP备2025076154号
"""


@app.on_event("startup")
async def _start_notifier():
    logger.info("应用启动中...")
    
    # 清理日志
    try:
        log_manager.cleanup()
    except Exception as e:
        logger.error(f"日志清理失败: {e}")
    
    # 启动通知循环
    asyncio.create_task(notifier_loop())
    
    logger.info("应用启动完成")

