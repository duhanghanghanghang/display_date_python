"""
统一API响应格式
"""
from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel
from fastapi import status
from fastapi.responses import JSONResponse


# 标准响应码
class ResponseCode:
    """响应状态码"""
    # 成功
    SUCCESS = 200
    
    # 客户端错误 4xx
    BAD_REQUEST = 400          # 请求参数错误
    UNAUTHORIZED = 401         # 未授权
    FORBIDDEN = 403            # 禁止访问
    NOT_FOUND = 404            # 资源不存在
    METHOD_NOT_ALLOWED = 405   # 方法不允许
    CONFLICT = 409             # 资源冲突
    UNPROCESSABLE = 422        # 无法处理的实体
    
    # 服务器错误 5xx
    INTERNAL_ERROR = 500       # 服务器内部错误
    SERVICE_UNAVAILABLE = 503  # 服务不可用


# 响应消息
class ResponseMessage:
    """响应消息常量"""
    SUCCESS = "操作成功"
    CREATED = "创建成功"
    UPDATED = "更新成功"
    DELETED = "删除成功"
    
    BAD_REQUEST = "请求参数错误"
    UNAUTHORIZED = "未授权，请先登录"
    FORBIDDEN = "无权限访问"
    NOT_FOUND = "资源不存在"
    
    INTERNAL_ERROR = "服务器内部错误"
    DATABASE_ERROR = "数据库操作失败"
    NETWORK_ERROR = "网络请求失败"


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应模型"""
    code: int = ResponseCode.SUCCESS
    message: str = ResponseMessage.SUCCESS
    data: Optional[T] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": {}
            }
        }


class ResponseUtil:
    """响应工具类"""
    
    @staticmethod
    def success(data: Any = None, message: str = ResponseMessage.SUCCESS, code: int = ResponseCode.SUCCESS) -> JSONResponse:
        """成功响应"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": code,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def created(data: Any = None, message: str = ResponseMessage.CREATED) -> JSONResponse:
        """创建成功响应"""
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "code": ResponseCode.SUCCESS,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def error(
        message: str = ResponseMessage.INTERNAL_ERROR,
        code: int = ResponseCode.INTERNAL_ERROR,
        data: Any = None,
        http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> JSONResponse:
        """错误响应"""
        return JSONResponse(
            status_code=http_status,
            content={
                "code": code,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def bad_request(message: str = ResponseMessage.BAD_REQUEST, data: Any = None) -> JSONResponse:
        """请求参数错误"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": ResponseCode.BAD_REQUEST,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def unauthorized(message: str = ResponseMessage.UNAUTHORIZED) -> JSONResponse:
        """未授权"""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "code": ResponseCode.UNAUTHORIZED,
                "message": message,
                "data": None
            }
        )
    
    @staticmethod
    def forbidden(message: str = ResponseMessage.FORBIDDEN) -> JSONResponse:
        """禁止访问"""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "code": ResponseCode.FORBIDDEN,
                "message": message,
                "data": None
            }
        )
    
    @staticmethod
    def not_found(message: str = ResponseMessage.NOT_FOUND) -> JSONResponse:
        """资源不存在"""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": ResponseCode.NOT_FOUND,
                "message": message,
                "data": None
            }
        )


# 便捷方法
def success_response(data: Any = None, message: str = ResponseMessage.SUCCESS) -> JSONResponse:
    """成功响应的便捷方法"""
    return ResponseUtil.success(data=data, message=message)


def error_response(message: str, code: int = ResponseCode.INTERNAL_ERROR, 
                  http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> JSONResponse:
    """错误响应的便捷方法"""
    return ResponseUtil.error(message=message, code=code, http_status=http_status)
