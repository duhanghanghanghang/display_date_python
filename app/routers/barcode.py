"""
条形码查询路由
"""
import requests
from fastapi import APIRouter, Depends, Query, HTTPException, status

from ..auth import get_current_openid
from ..logger import logger
from ..response import success_response, error_response, ResponseCode

router = APIRouter(prefix="/barcode", tags=["barcode"])


def query_barcode_api(barcode: str) -> dict:
    """
    查询条形码信息（使用 Open Food Facts 免费API）
    
    实际使用时可替换为其他商业API服务
    """
    try:
        # Open Food Facts API（免费，主要覆盖食品类）
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 1:  # 找到商品
                product = data.get('product', {})
                
                # 提取商品名称（优先中文）
                name = (product.get('product_name_zh') or 
                       product.get('product_name') or 
                       product.get('generic_name') or 
                       '未知商品')
                
                return {
                    'found': True,
                    'name': name,
                    'brand': product.get('brands', ''),
                    'category': product.get('categories', ''),
                    'image': product.get('image_url', ''),
                    'barcode': barcode
                }
        
        return {'found': False, 'barcode': barcode}
        
    except Exception as e:
        logger.error(f"查询条形码失败: {e}")
        return {'found': False, 'barcode': barcode}


@router.get("/query")
async def query_barcode(
    code: str = Query(..., description="条形码"),
    openid: str = Depends(get_current_openid)
):
    """
    查询条形码对应的商品信息
    
    - 支持 EAN-13、EAN-8 等标准条形码
    - 返回商品名称、图片等信息
    - 使用免费的 Open Food Facts 数据库（主要覆盖食品类）
    """
    try:
        if not code or len(code) < 8:
            return error_response(
                message="条形码格式错误",
                code=ResponseCode.BAD_REQUEST,
                http_status=status.HTTP_400_BAD_REQUEST
            )
        
        # 查询商品信息
        result = query_barcode_api(code)
        
        if result['found']:
            logger.info(f"条形码查询成功: {code}, 商品: {result['name']}")
            return success_response(
                data=result,
                message="查询成功"
            )
        else:
            return success_response(
                data={'found': False, 'barcode': code},
                message="未找到该商品信息，请手动填写"
            )
            
    except Exception as e:
        logger.error(f"查询条形码异常: {e}", exc_info=True)
        return error_response(
            message="查询失败，请重试",
            code=ResponseCode.INTERNAL_ERROR,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
