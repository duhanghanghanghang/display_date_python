# 小程序优化方案

## 📋 需求清单

1. ✅ 优化Toast提示停留时间
2. ✅ 去掉首页过期商品提示
3. ✅ 添加商品图片上传功能（含压缩）
4. ✅ 条形码扫描识别商品功能

---

## 1. Toast提示停留时间优化

### 📊 业界标准参考

根据微信、支付宝、美团等优秀小程序的实践：

| 提示类型 | 停留时间 | 使用场景 | 示例 |
|---------|---------|---------|------|
| **快速反馈** | 1500ms (1.5秒) | 简单操作完成 | "已复制"、"已删除" |
| **成功提示** | 2000ms (2秒) | 重要操作成功 | "保存成功"、"创建成功" |
| **警告/提醒** | 3000ms (3秒) | 需要注意的信息 | "请填写完整信息"、"网络连接失败" |
| **错误提示** | 3000ms (3秒) | 操作失败 | "保存失败"、"登录失败" |
| **信息提示** | 2500ms (2.5秒) | 一般信息展示 | "加载中..."、"数据已同步" |

### 🎯 统一Toast工具类

创建 `utils/toast.js`：

```javascript
/**
 * 统一Toast提示工具
 * 根据业界最佳实践制定停留时间
 */

const ToastType = {
  SUCCESS: 'success',    // 成功
  ERROR: 'error',        // 错误
  WARNING: 'none',       // 警告
  INFO: 'none',          // 信息
  LOADING: 'loading'     // 加载中
}

const ToastDuration = {
  QUICK: 1500,    // 快速反馈（1.5秒）
  SHORT: 2000,    // 短时间（2秒）
  MEDIUM: 2500,   // 中等时间（2.5秒）
  LONG: 3000      // 长时间（3秒）
}

class Toast {
  /**
   * 快速反馈 - 简单操作完成
   * @param {string} title 
   */
  static quick(title) {
    wx.showToast({
      title,
      icon: 'success',
      duration: ToastDuration.QUICK
    })
  }

  /**
   * 成功提示 - 重要操作成功
   * @param {string} title 
   */
  static success(title) {
    wx.showToast({
      title,
      icon: 'success',
      duration: ToastDuration.SHORT
    })
  }

  /**
   * 错误提示
   * @param {string} title 
   */
  static error(title) {
    wx.showToast({
      title,
      icon: 'error',
      duration: ToastDuration.LONG
    })
  }

  /**
   * 警告提示
   * @param {string} title 
   */
  static warning(title) {
    wx.showToast({
      title,
      icon: 'none',
      duration: ToastDuration.LONG
    })
  }

  /**
   * 信息提示
   * @param {string} title 
   */
  static info(title) {
    wx.showToast({
      title,
      icon: 'none',
      duration: ToastDuration.MEDIUM
    })
  }

  /**
   * 加载提示
   * @param {string} title 
   */
  static loading(title = '加载中...') {
    wx.showLoading({
      title,
      mask: true
    })
  }

  /**
   * 隐藏Loading
   */
  static hide() {
    wx.hideLoading()
  }
}

module.exports = { Toast, ToastType, ToastDuration }
```

### 📝 使用示例

```javascript
const { Toast } = require('../../utils/toast')

// 快速反馈
Toast.quick('已复制')

// 成功提示
Toast.success('保存成功')

// 错误提示
Toast.error('保存失败，请重试')

// 警告提示
Toast.warning('请填写完整信息')

// 信息提示
Toast.info('数据已同步')

// 加载中
Toast.loading('正在上传...')
// ... 操作完成后
Toast.hide()
```

---

## 2. 去掉首页过期商品提示

### 问题代码位置

#### 位置1：`app.js` 第66行和第86-124行

```javascript
// app.js
async onShow() {
  // 每次显示页面时刷新数据
  app.checkExpiredItems()  // ❌ 删除这行
  await this.initTeam()
  this.loadItems()
},

// 同时删除 checkExpiredItems 整个方法（第86-124行）
```

#### 位置2：`pages/index/index.js` 第66行

```javascript
// pages/index/index.js
async onShow() {
  // 每次显示页面时刷新数据
  app.checkExpiredItems()  // ❌ 删除这行
  await this.initTeam()
  this.loadItems()
},
```

### 修改方案

**方式1：完全删除（推荐）**

直接删除所有调用和方法定义。

**方式2：保留功能，改为手动触发**

在"我的"页面添加一个"检查过期商品"按钮，用户主动点击时才提示。

**方式3：静默统计**

保留统计逻辑，但不显示Toast，只在界面上显示数字标识。

### 推荐实施

采用方式1，完全删除自动提示，改为：
1. 在首页顶部显示过期商品数量（红色角标）
2. 用户点击筛选时可以看到过期商品列表
3. 不再弹出Toast打扰用户

---

## 3. 商品图片上传功能

### 架构设计

```
[小程序端] → [图片选择] → [图片压缩] → [上传到后端] → [OSS/本地存储] → [返回URL]
```

### 3.1 后端实现

#### 方式A：直接存储到服务器（适合小规模）

**优点**：
- 简单，无需第三方服务
- 成本低

**缺点**：
- 占用服务器存储
- 带宽压力大

#### 方式B：使用OSS对象存储（推荐）

**优点**：
- 专业CDN加速
- 存储成本低
- 不占用服务器资源

**推荐服务**：
- 阿里云OSS（99元/年起）
- 腾讯云COS（100GB/月 免费额度）
- 七牛云（10GB 免费额度）

### 3.2 后端代码（方式A：本地存储）

在 `display_date_python` 项目中添加：

#### 安装依赖

```bash
pip install Pillow==10.1.0
```

更新 `requirements.txt`：
```
Pillow==10.1.0
```

#### 创建上传接口

`app/routers/upload.py`：

```python
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


def ensure_upload_dir():
    """确保上传目录存在"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
```

#### 注册路由

在 `app/main.py` 中添加：

```python
from .routers import auth, items, teams, notify, webhook, upload

app.include_router(upload.router)
```

#### 配置静态文件服务

在 `app/main.py` 中添加：

```python
from fastapi.staticfiles import StaticFiles

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

### 3.3 小程序端实现

#### 图片压缩工具

创建 `utils/imageCompressor.js`：

```javascript
/**
 * 图片压缩工具
 * 在上传前压缩图片，减少流量消耗
 */

class ImageCompressor {
  /**
   * 压缩图片
   * @param {string} filePath 临时文件路径
   * @param {object} options 压缩选项
   * @returns {Promise<string>} 压缩后的临时文件路径
   */
  static async compress(filePath, options = {}) {
    const {
      quality = 80,        // 质量 (0-100)
      maxWidth = 1200,     // 最大宽度
      maxHeight = 1200,    // 最大高度
    } = options

    try {
      // 获取图片信息
      const info = await this.getImageInfo(filePath)
      
      // 计算压缩后的尺寸
      const { width, height } = this.calculateSize(
        info.width,
        info.height,
        maxWidth,
        maxHeight
      )

      // 压缩图片
      const compressed = await this.compressImage(filePath, {
        quality,
        width,
        height
      })

      return compressed
    } catch (error) {
      console.error('压缩图片失败:', error)
      // 压缩失败则返回原图
      return filePath
    }
  }

  /**
   * 获取图片信息
   */
  static getImageInfo(src) {
    return new Promise((resolve, reject) => {
      wx.getImageInfo({
        src,
        success: resolve,
        fail: reject
      })
    })
  }

  /**
   * 计算压缩后的尺寸
   */
  static calculateSize(width, height, maxWidth, maxHeight) {
    let newWidth = width
    let newHeight = height

    if (width > maxWidth || height > maxHeight) {
      const ratio = Math.min(maxWidth / width, maxHeight / height)
      newWidth = Math.round(width * ratio)
      newHeight = Math.round(height * ratio)
    }

    return { width: newWidth, height: newHeight }
  }

  /**
   * 使用Canvas压缩图片
   */
  static compressImage(src, options) {
    return new Promise((resolve, reject) => {
      const canvas = wx.createOffscreenCanvas({
        type: '2d',
        width: options.width,
        height: options.height
      })

      const ctx = canvas.getContext('2d')
      const img = canvas.createImage()

      img.onload = () => {
        ctx.drawImage(img, 0, 0, options.width, options.height)
        
        canvas.toTempFilePath({
          fileType: 'jpg',
          quality: options.quality / 100,
          success: (res) => resolve(res.tempFilePath),
          fail: reject
        })
      }

      img.onerror = reject
      img.src = src
    })
  }

  /**
   * 批量压缩
   */
  static async compressMultiple(filePaths, options = {}) {
    const promises = filePaths.map(path => this.compress(path, options))
    return Promise.all(promises)
  }
}

module.exports = { ImageCompressor }
```

#### 图片上传功能

在 `pages/add/add.js` 中添加：

```javascript
const { request } = require('../../utils/request')
const { ImageCompressor } = require('../../utils/imageCompressor')
const { Toast } = require('../../utils/toast')

Page({
  data: {
    productImage: '',  // 商品图片URL
    // ... 其他字段
  },

  /**
   * 选择商品图片
   */
  async chooseProductImage() {
    try {
      // 选择图片
      const res = await wx.chooseMedia({
        count: 1,
        mediaType: ['image'],
        sourceType: ['album', 'camera'],
        sizeType: ['original']
      })

      if (!res.tempFiles || res.tempFiles.length === 0) {
        return
      }

      const tempFile = res.tempFiles[0]
      const tempFilePath = tempFile.tempFilePath

      // 显示加载提示
      Toast.loading('正在上传...')

      // 压缩图片
      const compressedPath = await ImageCompressor.compress(tempFilePath, {
        quality: 80,
        maxWidth: 1200,
        maxHeight: 1200
      })

      // 上传到服务器
      const uploadRes = await this.uploadImage(compressedPath)

      // 更新数据
      this.setData({
        productImage: uploadRes.url
      })

      Toast.success('上传成功')
    } catch (error) {
      console.error('上传图片失败:', error)
      Toast.error('上传失败，请重试')
    }
  },

  /**
   * 上传图片到服务器
   */
  uploadImage(filePath) {
    return new Promise((resolve, reject) => {
      const openid = wx.getStorageSync('openid')
      const BASE_URL = require('../../config/env').apiBaseUrl

      wx.uploadFile({
        url: `${BASE_URL}/upload/product-image`,
        filePath,
        name: 'file',
        header: {
          'X-OpenId': openid
        },
        success: (res) => {
          if (res.statusCode === 200) {
            const data = JSON.parse(res.data)
            if (data.code === 200) {
              resolve(data.data)
            } else {
              reject(new Error(data.message))
            }
          } else {
            reject(new Error('上传失败'))
          }
        },
        fail: reject
      })
    })
  },

  /**
   * 预览商品图片
   */
  previewProductImage() {
    if (!this.data.productImage) return

    const BASE_URL = require('../../config/env').apiBaseUrl
    const imageUrl = `${BASE_URL}${this.data.productImage}`

    wx.previewImage({
      urls: [imageUrl],
      current: imageUrl
    })
  },

  /**
   * 删除商品图片
   */
  deleteProductImage() {
    wx.showModal({
      title: '提示',
      content: '确定要删除这张图片吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({
            productImage: ''
          })
          Toast.quick('已删除')
        }
      }
    })
  }
})
```

#### WXML模板

在 `pages/add/add.wxml` 中添加：

```xml
<!-- 商品图片 -->
<view class="form-section">
  <view class="section-title">商品图片（选填）</view>
  
  <view class="image-upload">
    <view wx:if="{{productImage}}" class="image-preview">
      <image 
        src="{{apiBaseUrl}}{{productImage}}" 
        mode="aspectFill"
        bindtap="previewProductImage"
      />
      <view class="image-delete" bindtap="deleteProductImage">
        <text class="icon-close">×</text>
      </view>
    </view>
    
    <view wx:else class="image-upload-btn" bindtap="chooseProductImage">
      <text class="icon-camera">📷</text>
      <text class="upload-text">添加图片</text>
    </view>
  </view>
</view>
```

#### WXSS样式

```css
.image-upload {
  padding: 20rpx 0;
}

.image-preview {
  position: relative;
  width: 200rpx;
  height: 200rpx;
  border-radius: 8rpx;
  overflow: hidden;
}

.image-preview image {
  width: 100%;
  height: 100%;
}

.image-delete {
  position: absolute;
  top: 0;
  right: 0;
  width: 50rpx;
  height: 50rpx;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-close {
  color: white;
  font-size: 40rpx;
  line-height: 1;
}

.image-upload-btn {
  width: 200rpx;
  height: 200rpx;
  border: 2rpx dashed #ddd;
  border-radius: 8rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f8f8f8;
}

.icon-camera {
  font-size: 60rpx;
  margin-bottom: 10rpx;
}

.upload-text {
  font-size: 24rpx;
  color: #999;
}
```

---

## 4. 条形码扫描识别商品

### 方案设计

```
[扫描条形码] → [获取条码] → [查询商品数据库] → [返回商品信息] → [自动填充]
```

### 4.1 条形码数据库方案

#### 方案A：中国物品编码中心 API（官方，推荐）

**服务**：国家物品编码中心（GS1 China）
**网站**：https://www.ancc.org.cn/
**特点**：
- 官方权威数据
- 需要申请API接口（有免费额度）
- 数据最全面

#### 方案B：第三方商品库API

**1. 京东万象API**
- 网站：https://wx.jdcloud.com/
- 商品条码查询API
- 付费服务（0.01元/次起）

**2. 聚合数据API**
- 网站：https://www.juhe.cn/
- 条码查询接口
- 付费服务（有免费试用）

**3. APISpace 条码查询**
- 网站：https://www.apispace.com/
- 免费额度：100次/天
- 付费：0.01元/次

#### 方案C：开源条形码数据库

**Open Food Facts**
- 网站：https://world.openfoodfacts.org/
- 完全免费
- 主要覆盖食品类
- API文档：https://wiki.openfoodfacts.org/API

#### 方案D：自建数据库

适合企业内部商品管理，不适合通用场景。

### 4.2 推荐实施方案

**短期（快速上线）**：
- 使用 APISpace 或聚合数据的免费额度
- 扫码后查询API获取商品信息
- 用户可手动修改补充

**长期（降低成本）**：
- 建立自己的商品缓存数据库
- 首次查询API后缓存结果
- 相同条码直接从缓存读取
- 定期更新缓存数据

### 4.3 实现代码

#### 后端接口

`app/routers/barcode.py`：

```python
"""
条形码查询路由
"""
import requests
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_openid
from ..database import get_db
from ..logger import logger
from ..response import success_response, error_response, ResponseCode
from ..config import settings

router = APIRouter(prefix="/barcode", tags=["barcode"])


def query_barcode_api(barcode: str) -> dict:
    """
    查询条形码信息（示例使用 Open Food Facts）
    
    实际使用时替换为你选择的API服务
    """
    try:
        # Open Food Facts API（免费）
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 1:  # 找到商品
                product = data.get('product', {})
                return {
                    'found': True,
                    'name': product.get('product_name') or product.get('product_name_zh') or '未知商品',
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
```

注册路由：

```python
# app/main.py
from .routers import barcode

app.include_router(barcode.router)
```

#### 小程序端实现

在 `pages/add/add.js` 中添加：

```javascript
const { request } = require('../../utils/request')
const { Toast } = require('../../utils/toast')

Page({
  data: {
    barcode: '',
    // ... 其他字段
  },

  /**
   * 扫描条形码
   */
  async scanBarcode() {
    try {
      // 调用扫码API
      const res = await wx.scanCode({
        onlyFromCamera: false,  // 允许从相册选择
        scanType: ['barCode']   // 只扫条形码
      })

      const barcode = res.result

      if (!barcode) {
        Toast.warning('未识别到条形码')
        return
      }

      // 保存条形码
      this.setData({ barcode })
      Toast.info('正在识别商品...')

      // 查询商品信息
      await this.queryBarcodeInfo(barcode)

    } catch (error) {
      console.error('扫码失败:', error)
      
      if (error.errMsg && error.errMsg.includes('cancel')) {
        // 用户取消扫码，不提示错误
        return
      }
      
      Toast.error('扫码失败，请重试')
    }
  },

  /**
   * 查询条形码对应的商品信息
   */
  async queryBarcodeInfo(barcode) {
    try {
      const data = await request({
        url: `/barcode/query?code=${barcode}`,
        method: 'GET'
      })

      if (data.found) {
        // 找到商品信息，自动填充
        this.setData({
          name: data.name || this.data.name,
          barcode: data.barcode,
          productImage: data.image || this.data.productImage,
          category: data.category ? this.extractCategory(data.category) : this.data.category
        })

        Toast.success('识别成功，已自动填充')
      } else {
        // 未找到商品信息
        Toast.info('未找到商品信息，请手动填写')
      }
    } catch (error) {
      console.error('查询商品信息失败:', error)
      Toast.warning('查询失败，请手动填写')
    }
  },

  /**
   * 从API返回的分类中提取本地分类
   */
  extractCategory(apiCategory) {
    const categories = this.data.categories
    const lower = apiCategory.toLowerCase()

    for (let cat of categories) {
      if (lower.includes(cat)) {
        return cat
      }
    }

    return '其他'
  }
})
```

#### WXML模板

```xml
<!-- 条形码扫描 -->
<view class="form-section">
  <view class="section-title">
    条形码（选填）
    <button class="scan-btn" bindtap="scanBarcode" size="mini">
      扫一扫
    </button>
  </view>
  
  <input 
    class="input" 
    type="text" 
    placeholder="点击扫一扫或手动输入" 
    value="{{barcode}}"
    bindinput="onBarcodeInput"
  />
</view>
```

#### WXSS样式

```css
.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.scan-btn {
  background: #07c160;
  color: white;
  border: none;
  border-radius: 4rpx;
  padding: 10rpx 20rpx;
}
```

---

## 📦 完整修改清单

### 需要新增的文件

**小程序端：**
1. `utils/toast.js` - Toast工具类
2. `utils/imageCompressor.js` - 图片压缩工具

**后端：**
1. `app/routers/upload.py` - 图片上传接口
2. `app/routers/barcode.py` - 条形码查询接口

### 需要修改的文件

**小程序端：**
1. `app.js` - 删除 `checkExpiredItems()` 调用和方法
2. `pages/index/index.js` - 删除 `checkExpiredItems()` 调用
3. `pages/add/add.js` - 添加图片上传和条形码扫描功能
4. `pages/add/add.wxml` - 添加图片和条形码UI
5. `pages/add/add.wxss` - 添加相关样式
6. `pages/edit/edit.js` - 同add.js
7. `pages/edit/edit.wxml` - 同add.wxml
8. `pages/edit/edit.wxss` - 同add.wxss

**后端：**
1. `requirements.txt` - 添加 Pillow 依赖
2. `app/main.py` - 注册新路由，挂载静态文件
3. `.gitignore` - 添加 `uploads/` 到忽略列表

---

## 🚀 实施步骤

### 第一步：Toast优化（30分钟）

1. 创建 `utils/toast.js`
2. 全局替换 `wx.showToast` 为 `Toast.xxx()`
3. 测试各种提示场景

### 第二步：去掉过期提示（10分钟）

1. 修改 `app.js`，删除 `checkExpiredItems()` 方法
2. 修改 `pages/index/index.js`，删除调用
3. 测试首页加载

### 第三步：图片上传（2小时）

1. 后端添加上传接口
2. 创建图片压缩工具
3. 修改添加/编辑页面
4. 测试上传流程

### 第四步：条形码识别（1小时）

1. 注册API服务（如APISpace）
2. 后端添加查询接口
3. 小程序添加扫码功能
4. 测试扫码识别

---

## 📊 预期效果

1. **用户体验提升**
   - Toast提示时间合理，看得清楚
   - 不再频繁打扰（去掉自动提示）
   - 添加商品更便捷（扫码+图片）

2. **功能完善**
   - 支持商品图片展示
   - 快速录入（扫码识别）
   - 数据更丰富

3. **性能优化**
   - 图片自动压缩，节省流量
   - 上传速度快

---

## ⚠️ 注意事项

1. **图片存储**
   - 定期清理无用图片
   - 建议配置图片CDN加速
   - 长期建议迁移到OSS

2. **条形码API**
   - 免费额度有限，注意监控
   - 建议添加缓存机制
   - 查询失败要有降级方案

3. **安全性**
   - 上传文件需要验证格式
   - 限制文件大小
   - 防止恶意上传

4. **兼容性**
   - 图片压缩需要Canvas 2D API
   - 部分老设备可能不支持
   - 做好降级处理

---

## 📞 技术支持

如有问题，请查看：
- 微信小程序官方文档
- FastAPI 文档
- Pillow 文档

---

**准备好开始实施了吗？我已经为你准备好了所有代码！** 🎉
