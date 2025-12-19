"""
中间件模块
- 请求日志记录
- 错误日志记录
- 请求耗时统计
- 统一异常处理
"""
import time
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .logger import logger
from .response import ResponseCode, ResponseMessage


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 记录请求开始
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"
        
        # 记录请求
        logger.info(f"请求开始 | {method} {url} | 客户端: {client_host}")
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算耗时
            process_time = time.time() - start_time
            
            # 记录响应
            logger.info(
                f"请求完成 | {method} {url} | "
                f"状态码: {response.status_code} | "
                f"耗时: {process_time:.3f}s"
            )
            
            # 添加响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as exc:
            # 计算耗时
            process_time = time.time() - start_time
            
            # 记录错误
            logger.error(
                f"请求异常 | {method} {url} | "
                f"耗时: {process_time:.3f}s | "
                f"错误: {str(exc)}\n"
                f"堆栈跟踪:\n{traceback.format_exc()}"
            )
            
            # 返回统一格式的错误响应
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "code": ResponseCode.INTERNAL_ERROR,
                    "message": ResponseMessage.INTERNAL_ERROR,
                    "data": {
                        "detail": str(exc) if logger.level == 10 else None
                    }
                }
            )
