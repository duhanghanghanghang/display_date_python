# API 响应格式规范

## 📋 统一响应格式

### 标准响应结构

所有API接口统一返回以下格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 业务状态码（见下方状态码表） |
| `message` | string | 响应消息，用于前端提示 |
| `data` | any | 响应数据，成功时包含实际数据，失败时可为 null 或错误详情 |

---

## 📊 状态码规范

### 成功状态码 (2xx)

| 状态码 | HTTP状态 | 说明 | 使用场景 |
|--------|----------|------|----------|
| 200 | 200 OK | 操作成功 | 查询、更新、删除成功 |
| 200 | 201 Created | 创建成功 | 创建资源成功 |

### 客户端错误 (4xx)

| 状态码 | HTTP状态 | 说明 | 使用场景 |
|--------|----------|------|----------|
| 400 | 400 Bad Request | 请求参数错误 | 参数验证失败、格式错误 |
| 401 | 401 Unauthorized | 未授权 | 未登录、token过期 |
| 403 | 403 Forbidden | 禁止访问 | 无权限操作资源 |
| 404 | 404 Not Found | 资源不存在 | 请求的资源未找到 |
| 409 | 409 Conflict | 资源冲突 | 资源已存在、状态冲突 |
| 422 | 422 Unprocessable | 无法处理 | 语义错误、业务逻辑错误 |

### 服务器错误 (5xx)

| 状态码 | HTTP状态 | 说明 | 使用场景 |
|--------|----------|------|----------|
| 500 | 500 Internal Error | 服务器内部错误 | 未预期的系统错误 |
| 503 | 503 Service Unavailable | 服务不可用 | 系统维护、过载 |

---

## 💡 响应示例

### 成功响应

#### 查询成功（返回列表）

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "items": [
      {
        "id": "123",
        "name": "商品A",
        "quantity": 5
      }
    ]
  }
}
```

#### 创建成功

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": "456",
    "name": "新商品",
    "createdAt": "2025-12-19T12:00:00Z"
  }
}
```

#### 更新成功

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": "123",
    "name": "更新后的商品"
  }
}
```

#### 删除成功

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

### 错误响应

#### 参数错误

```json
{
  "code": 400,
  "message": "请求参数错误",
  "data": {
    "detail": "商品名称不能为空"
  }
}
```

#### 未授权

```json
{
  "code": 401,
  "message": "未授权，请先登录",
  "data": null
}
```

#### 资源不存在

```json
{
  "code": 404,
  "message": "商品不存在",
  "data": null
}
```

#### 无权限

```json
{
  "code": 403,
  "message": "无权限访问该资源",
  "data": null
}
```

#### 服务器错误

```json
{
  "code": 500,
  "message": "服务器内部错误",
  "data": {
    "detail": "数据库连接失败"
  }
}
```

---

## 🔧 后端使用指南

### 导入响应工具

```python
from app.response import (
    ResponseUtil,
    success_response,
    error_response,
    ResponseCode,
    ResponseMessage
)
```

### 成功响应

```python
from fastapi import APIRouter
from app.response import success_response

router = APIRouter()

@router.get("/items")
def get_items():
    items = [{"id": "1", "name": "商品A"}]
    return success_response(
        data={"items": items},
        message="获取成功"
    )
```

### 创建成功

```python
@router.post("/items")
def create_item(item: ItemCreate):
    new_item = create_item_in_db(item)
    return ResponseUtil.created(
        data=new_item,
        message="创建成功"
    )
```

### 错误响应

```python
from fastapi import HTTPException
from app.response import ResponseCode, error_response

@router.get("/items/{item_id}")
def get_item(item_id: str):
    item = find_item(item_id)
    if not item:
        return error_response(
            message="商品不存在",
            code=ResponseCode.NOT_FOUND,
            http_status=404
        )
    return success_response(data=item)
```

### 使用便捷方法

```python
from app.response import ResponseUtil

# 400 错误
return ResponseUtil.bad_request("参数错误")

# 401 错误
return ResponseUtil.unauthorized("请先登录")

# 403 错误
return ResponseUtil.forbidden("无权限")

# 404 错误
return ResponseUtil.not_found("资源不存在")
```

---

## 📱 小程序端使用指南

### 通用请求处理

```javascript
// utils/request.js
const request = (url, options = {}) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}${url}`,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'X-OpenId': wx.getStorageSync('openid'),
        'Content-Type': 'application/json',
        ...options.header
      },
      success: (res) => {
        const { code, message, data } = res.data;
        
        // 统一处理响应
        if (code === 200) {
          resolve(data);
        } else {
          // 显示错误提示
          wx.showToast({
            title: message || '操作失败',
            icon: 'none'
          });
          
          // 特殊错误处理
          if (code === 401) {
            // 未授权，跳转登录
            wx.navigateTo({ url: '/pages/login/login' });
          }
          
          reject(new Error(message));
        }
      },
      fail: (err) => {
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        });
        reject(err);
      }
    });
  });
};

module.exports = { request };
```

### 使用示例

```javascript
// pages/items/items.js
const { request } = require('../../utils/request');

Page({
  data: {
    items: []
  },
  
  onLoad() {
    this.loadItems();
  },
  
  async loadItems() {
    try {
      // 请求会自动处理统一格式
      const data = await request('/items', {
        method: 'GET'
      });
      
      // data 已经是解包后的数据
      this.setData({
        items: data.items || []
      });
    } catch (error) {
      console.error('加载失败:', error);
      // 错误已经在 request 中显示了
    }
  },
  
  async createItem(itemData) {
    try {
      const data = await request('/items', {
        method: 'POST',
        data: itemData
      });
      
      wx.showToast({
        title: '创建成功',
        icon: 'success'
      });
      
      // 刷新列表
      this.loadItems();
    } catch (error) {
      // 错误已处理
    }
  }
});
```

### 错误处理增强

```javascript
// utils/request.js (增强版)
const ERROR_MESSAGES = {
  400: '请求参数有误',
  401: '请先登录',
  403: '无权限访问',
  404: '资源不存在',
  500: '服务器错误',
  503: '服务暂不可用'
};

const request = (url, options = {}) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}${url}`,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'X-OpenId': wx.getStorageSync('openid'),
        'Content-Type': 'application/json',
        ...options.header
      },
      success: (res) => {
        const { code, message, data } = res.data;
        
        if (code === 200) {
          resolve(data);
        } else {
          // 使用自定义消息或默认消息
          const errorMsg = message || ERROR_MESSAGES[code] || '操作失败';
          
          wx.showToast({
            title: errorMsg,
            icon: 'none',
            duration: 2000
          });
          
          // 特殊状态处理
          switch (code) {
            case 401:
              // 清除登录态
              wx.removeStorageSync('openid');
              // 跳转登录（延迟以显示提示）
              setTimeout(() => {
                wx.reLaunch({ url: '/pages/login/login' });
              }, 2000);
              break;
            case 403:
              // 无权限，返回上一页
              setTimeout(() => {
                wx.navigateBack();
              }, 2000);
              break;
          }
          
          reject({ code, message: errorMsg, data });
        }
      },
      fail: (err) => {
        console.error('网络请求失败:', err);
        wx.showToast({
          title: '网络连接失败',
          icon: 'none'
        });
        reject(err);
      }
    });
  });
};
```

---

## 🔄 迁移指南

### 旧接口格式（需要修改）

```python
# ❌ 旧格式 - 直接返回数据
@router.get("/items")
def get_items():
    return {"items": [...]}

# ❌ 旧格式 - 使用 HTTPException
@router.get("/items/{item_id}")
def get_item(item_id: str):
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item
```

### 新接口格式（推荐）

```python
# ✅ 新格式 - 统一响应
from app.response import success_response, error_response, ResponseCode

@router.get("/items")
def get_items():
    items = get_items_from_db()
    return success_response(
        data={"items": items},
        message="获取成功"
    )

@router.get("/items/{item_id}")
def get_item(item_id: str):
    item = find_item(item_id)
    if not item:
        return error_response(
            message="商品不存在",
            code=ResponseCode.NOT_FOUND,
            http_status=404
        )
    return success_response(data=item)
```

### 小程序端迁移

#### 旧代码

```javascript
// ❌ 旧代码 - 直接使用 res.data
wx.request({
  url: API_BASE_URL + '/items',
  success: (res) => {
    this.setData({ items: res.data.items });
  }
});
```

#### 新代码

```javascript
// ✅ 新代码 - 使用统一请求函数
const { request } = require('../../utils/request');

const data = await request('/items');
this.setData({ items: data.items });
```

---

## 🎯 最佳实践

### 1. 始终返回统一格式

```python
# ✅ 正确
return success_response(data={"id": "123"})

# ❌ 错误
return {"id": "123"}
```

### 2. 使用有意义的消息

```python
# ✅ 正确
return error_response(message="商品名称不能为空", code=400)

# ❌ 错误
return error_response(message="Error", code=400)
```

### 3. 合理使用状态码

```python
# ✅ 正确 - 使用预定义常量
return error_response(
    message="资源不存在",
    code=ResponseCode.NOT_FOUND,
    http_status=404
)

# ❌ 错误 - 硬编码
return error_response(message="Not found", code=404, http_status=404)
```

### 4. data 字段的使用

```python
# ✅ 列表数据 - 包装在对象中
return success_response(data={"items": [...]})

# ✅ 单个对象
return success_response(data={"id": "123", "name": "商品A"})

# ✅ 无数据返回
return success_response(data=None, message="删除成功")

# ❌ 错误 - 直接返回列表
return success_response(data=[...])
```

---

## 📚 参考资料

- RESTful API 设计规范
- HTTP 状态码标准
- FastAPI 响应模型文档

---

**统一响应格式让前后端协作更加顺畅！** 🚀
