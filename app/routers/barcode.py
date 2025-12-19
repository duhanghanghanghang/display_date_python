"""
条形码查询路由
"""
import requests
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query, HTTPException, status

from ..auth import get_current_openid
from ..logger import logger
from ..response import success_response, error_response, ResponseCode
from ..database import get_db
from ..models import Product

router = APIRouter(prefix="/barcode", tags=["barcode"])

# 本地简易商品数据库（常见中国商品）
LOCAL_BARCODE_DB = {
    '6902363560351': {'name': '得宝(Tempo)纸巾', 'brand': '得宝', 'category': '纸巾'},
    '6901028075916': {'name': '可口可乐', 'brand': '可口可乐', 'category': '饮料'},
    '6922255451062': {'name': '旺旺雪饼', 'brand': '旺旺', 'category': '零食'},
    '6901939535943': {'name': '康师傅红烧牛肉面', 'brand': '康师傅', 'category': '食品'},
    '6970243720010': {'name': '三只松鼠坚果', 'brand': '三只松鼠', 'category': '零食'},
}


def query_local_database(barcode: str) -> dict:
    """
    查询本地数据库
    """
    if barcode in LOCAL_BARCODE_DB:
        data = LOCAL_BARCODE_DB[barcode]
        return {
            'found': True,
            'name': data['name'],
            'brand': data.get('brand', ''),
            'category': data.get('category', ''),
            'image': '',
            'barcode': barcode,
            'source': 'local'
        }
    return {'found': False, 'barcode': barcode}


def query_openfoodfacts(barcode: str) -> dict:
    """
    查询 Open Food Facts API
    """
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 1:
                product = data.get('product', {})
                name = (product.get('product_name_zh') or 
                       product.get('product_name') or 
                       product.get('generic_name'))
                
                if name and name != 'unknown':
                    return {
                        'found': True,
                        'name': name,
                        'brand': product.get('brands', ''),
                        'category': product.get('categories', ''),
                        'image': product.get('image_url', ''),
                        'barcode': barcode,
                        'source': 'openfoodfacts'
                    }
    except Exception as e:
        logger.warning(f"Open Food Facts 查询失败: {e}")
    
    return {'found': False, 'barcode': barcode}


def query_upcitemdb(barcode: str) -> dict:
    """
    查询 UPCitemdb API（免费版每天100次）
    """
    try:
        url = f"https://api.upcitemdb.com/prod/trial/lookup"
        params = {'upc': barcode}
        headers = {'Accept': 'application/json'}
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == 'OK' and data.get('items'):
                item = data['items'][0]
                return {
                    'found': True,
                    'name': item.get('title', ''),
                    'brand': item.get('brand', ''),
                    'category': item.get('category', ''),
                    'image': item.get('images', [''])[0] if item.get('images') else '',
                    'barcode': barcode,
                    'source': 'upcitemdb'
                }
    except Exception as e:
        logger.warning(f"UPCitemdb 查询失败: {e}")
    
    return {'found': False, 'barcode': barcode}


def save_product_to_db(db: Session, barcode: str, product_data: dict) -> Product:
    """
    保存商品到数据库
    """
    try:
        product = Product(
            barcode=barcode,
            name=product_data.get('name', ''),
            brand=product_data.get('brand', ''),
            category=product_data.get('category', ''),
            image=product_data.get('image', ''),
            source=product_data.get('source', 'unknown'),
            query_count=1,
            last_queried_at=datetime.now()
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        logger.info(f"商品已保存到数据库: {barcode} - {product.name}")
        return product
    except Exception as e:
        db.rollback()
        logger.error(f"保存商品到数据库失败: {e}")
        return None


def update_product_query_stats(db: Session, product: Product):
    """
    更新商品查询统计
    """
    try:
        product.query_count += 1
        product.last_queried_at = datetime.now()
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"更新商品统计失败: {e}")


def query_database(db: Session, barcode: str) -> dict:
    """
    查询数据库中的商品
    """
    try:
        product = db.query(Product).filter(Product.barcode == barcode).first()
        if product:
            # 更新查询统计
            update_product_query_stats(db, product)
            
            return {
                'found': True,
                'name': product.name,
                'brand': product.brand or '',
                'category': product.category or '',
                'image': product.image or '',
                'barcode': product.barcode,
                'source': f'database({product.source})'
            }
    except Exception as e:
        logger.error(f"数据库查询失败: {e}")
    
    return {'found': False, 'barcode': barcode}


def query_barcode_api(db: Session, barcode: str) -> dict:
    """
    组合多个数据源查询条形码信息
    
    查询顺序：
    1. 数据库（已缓存的商品）
    2. 本地静态数据（常见商品）
    3. Open Food Facts（免费，食品类）
    4. UPCitemdb（免费，每天100次）
    
    如果API找到了商品，自动保存到数据库
    """
    # 1. 先查数据库
    result = query_database(db, barcode)
    if result['found']:
        logger.info(f"数据库找到商品: {barcode}")
        return result
    
    # 2. 查本地静态数据
    result = query_local_database(barcode)
    if result['found']:
        logger.info(f"本地静态数据找到商品: {barcode}")
        # 保存到数据库
        save_product_to_db(db, barcode, result)
        return result
    
    # 3. 查询 Open Food Facts
    result = query_openfoodfacts(barcode)
    if result['found']:
        logger.info(f"Open Food Facts找到商品: {barcode}")
        # 保存到数据库
        save_product_to_db(db, barcode, result)
        return result
    
    # 4. 查询 UPCitemdb
    result = query_upcitemdb(barcode)
    if result['found']:
        logger.info(f"UPCitemdb找到商品: {barcode}")
        # 保存到数据库
        save_product_to_db(db, barcode, result)
        return result
    
    # 都没找到
    logger.warning(f"所有数据源都未找到商品: {barcode}")
    return {'found': False, 'barcode': barcode}


@router.get("/query")
async def query_barcode(
    code: str = Query(..., description="条形码"),
    openid: str = Depends(get_current_openid),
    db: Session = Depends(get_db)
):
    """
    查询条形码对应的商品信息
    
    - 支持 EAN-13、EAN-8 等标准条形码
    - 优先从数据库查询（快速）
    - 数据库没有则从免费API查询并自动缓存
    - 返回商品名称、品牌、分类、图片等信息
    """
    try:
        if not code or len(code) < 8:
            return error_response(
                message="条形码格式错误",
                code=ResponseCode.BAD_REQUEST,
                http_status=status.HTTP_400_BAD_REQUEST
            )
        
        # 查询商品信息（会自动保存到数据库）
        result = query_barcode_api(db, code)
        
        if result['found']:
            logger.info(f"条形码查询成功: {code}, 商品: {result['name']}")
            return success_response(
                data=result,
                message="查询成功"
            )
        else:
            # 未找到商品信息，但返回条形码
            logger.warning(f"条形码未找到商品: {code}")
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
