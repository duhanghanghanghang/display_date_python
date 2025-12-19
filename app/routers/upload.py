"""
图片上传路由
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from PIL import Image
import io

from ..auth import get_current_openid
from ..logger import logger
from ..response import success_response, error_response, ResponseCode

router = APIRouter(prefix="/upload", tags=["upload"])

# 上传配置
UPLOAD_DIR = Path("uploads/products")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = (1920, 1920)  # 最大尺寸


def compress_image(image_data: bytes, max_size: tuple = (800, 800), quality: int = 85) -> bytes:
    """
    压缩图片
    
    Args:
        image_data: 原始图片数据
        max_size: 最大尺寸 (width, height)
        quality: JPEG质量 (1-100)
    
    Returns:
        压缩后的图片数据
    """
    try:
        # 打开图片
        image = Image.open(io.BytesIO(image_data))
        
        # 转换RGBA到RGB（处理PNG透明背景）
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 计算缩放比例
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 保存为JPEG
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        
        return output.getvalue()
    except Exception as e:
        logger.error(f"压缩图片失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="图片格式错误或损坏"
        )


@router.post("/product-image")
async def upload_product_image(
    file: UploadFile = File(...),
    openid: str = Depends(get_current_openid)
):
    """
    上传商品图片
    
    - 支持 jpg, jpeg, png, webp 格式
    - 自动压缩到合适大小
    - 返回图片URL
    """
    try:
        # 检查文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return error_response(
                message=f"不支持的文件格式，仅支持: {', '.join(ALLOWED_EXTENSIONS)}",
                code=ResponseCode.BAD_REQUEST,
                http_status=status.HTTP_400_BAD_REQUEST
            )
        
        # 读取文件内容
        file_data = await file.read()
        file_size = len(file_data)
        
        # 检查文件大小
        if file_size > MAX_FILE_SIZE:
            return error_response(
                message=f"文件过大，最大支持 {MAX_FILE_SIZE / 1024 / 1024:.0f}MB",
                code=ResponseCode.BAD_REQUEST,
                http_status=status.HTTP_400_BAD_REQUEST
            )
        
        # 压缩图片
        compressed_data = compress_image(file_data)
        
        # 生成文件名：日期/UUID.jpg
        date_dir = datetime.now().strftime('%Y%m')
        file_name = f"{uuid.uuid4().hex}.jpg"
        
        # 确保目录存在
        save_dir = UPLOAD_DIR / date_dir
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = save_dir / file_name
        with open(file_path, 'wb') as f:
            f.write(compressed_data)
        
        # 生成访问URL（相对路径）
        relative_path = f"/uploads/products/{date_dir}/{file_name}"
        
        logger.info(f"图片上传成功: {relative_path}, 用户: {openid}, 原始大小: {file_size/1024:.1f}KB, 压缩后: {len(compressed_data)/1024:.1f}KB")
        
        return success_response(
            data={
                "url": relative_path,
                "filename": file_name,
                "size": len(compressed_data)
            },
            message="上传成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传图片失败: {e}", exc_info=True)
        return error_response(
            message="上传失败，请重试",
            code=ResponseCode.INTERNAL_ERROR,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
