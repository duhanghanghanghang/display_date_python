# 小程序功能实施指南

## 📋 实施清单

本文档提供具体的代码修改步骤，按顺序执行即可完成所有功能。

---

## ✅ 第1步：优化Toast提示时间（已完成）

### 已创建文件

- ✅ `/Users/d/Desktop/2/display_date/utils/toast.js`

### 使用方法

在所有页面 JS 文件顶部添加：

```javascript
const { Toast } = require('../../utils/toast')
```

然后全局替换 Toast 调用（示例）：

```javascript
// ❌ 旧代码
wx.showToast({ title: '保存成功', icon: 'success' })
wx.showToast({ title: '保存失败', icon: 'none' })
wx.showToast({ title: '已复制', icon: 'success' })

// ✅ 新代码
Toast.success('保存成功')        // 2秒
Toast.error('保存失败')          // 3秒
Toast.quick('已复制')            // 1.5秒
Toast.warning('请填写完整信息')  // 3秒
Toast.info('数据已同步')         // 2.5秒
```

### 批量替换建议

| 旧代码场景 | 新方法 | 停留时间 |
|-----------|--------|---------|
| 创建/保存/更新成功 | `Toast.success()` | 2秒 |
| 操作失败/网络错误 | `Toast.error()` | 3秒 |
| 已复制/已删除/已切换 | `Toast.quick()` | 1.5秒 |
| 权限不足/参数错误 | `Toast.warning()` | 3秒 |
| 一般信息提示 | `Toast.info()` | 2.5秒 |

---

## ✅ 第2步：去掉首页过期商品提示（已完成）

### 已修改文件

- ✅ `/Users/d/Desktop/2/display_date/app.js` - 注释掉第22行
- ✅ `/Users/d/Desktop/2/display_date/pages/index/index.js` - 注释掉第66行

### 效果

- ✅ 首页加载时不再弹出"xx件商品已过期"提示
- ✅ 保留了过期统计功能（在页面数据中）
- ✅ 用户可以通过筛选查看过期商品

### 可选优化

在首页顶部添加过期商品数量显示（静默提示）：

```xml
<!-- pages/index/index.wxml -->
<view class="stats-bar">
  <view class="stat-item" wx:if="{{expiredCount > 0}}">
    <text class="stat-label expired">已过期</text>
    <text class="stat-value">{{expiredCount}}</text>
  </view>
  <view class="stat-item" wx:if="{{warningCount > 0}}">
    <text class="stat-label warning">即将过期</text>
    <text class="stat-value">{{warningCount}}</text>
  </view>
</view>
```

---

## ✅ 第3步：商品图片上传功能

### 后端（已完成）

#### 已创建文件

- ✅ `app/routers/upload.py` - 图片上传接口
- ✅ `app/routers/barcode.py` - 条形码查询接口
- ✅ `app/main.py` - 已注册路由和静态文件服务
- ✅ `requirements.txt` - 已添加 Pillow 依赖
- ✅ `.gitignore` - 已添加 uploads/ 忽略规则

#### 新增接口

- `POST /upload/product-image` - 上传商品图片
- `GET /barcode/query?code=xxx` - 查询条形码

#### 测试后端

```bash
# 安装新依赖
cd /Users/d/Desktop/2/display_date_python
pip install -r requirements.txt

# 测试导入
python3 -c "from app.main import app; print('✅ 导入成功')"

# 启动服务
python3 run.py
```

### 小程序端（待实施）

#### 已创建文件

- ✅ `utils/imageCompressor.js` - 图片压缩工具

#### 需要修改的文件

**1. pages/add/add.js**

在文件顶部添加：

```javascript
const { Toast } = require('../../utils/toast')
const { ImageCompressor } = require('../../utils/imageCompressor')
const { apiBaseUrl } = require('../../config/env')
```

在 `data` 中确保有：

```javascript
data: {
  productImage: '',  // 商品图片URL
  // ... 其他字段
}
```

添加以下方法：

```javascript
/**
 * 选择商品图片
 */
async chooseProductImage() {
  try {
    const res = await wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera']
    })

    if (!res.tempFiles || res.tempFiles.length === 0) return

    const tempFilePath = res.tempFiles[0].tempFilePath

    Toast.loading('正在上传...')

    // 压缩图片
    const compressedPath = await ImageCompressor.compress(tempFilePath, {
      quality: 80,
      maxWidth: 1200,
      maxHeight: 1200
    })

    // 上传到服务器
    const uploadRes = await this.uploadImage(compressedPath)

    this.setData({ productImage: uploadRes.url })
    Toast.success('上传成功')
  } catch (error) {
    console.error('上传图片失败:', error)
    Toast.error('上传失败')
  }
},

/**
 * 上传图片到服务器
 */
uploadImage(filePath) {
  return new Promise((resolve, reject) => {
    const openid = wx.getStorageSync('openid')

    wx.uploadFile({
      url: `${apiBaseUrl}/upload/product-image`,
      filePath,
      name: 'file',
      header: { 'X-OpenId': openid },
      success: (res) => {
        Toast.hide()
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
      fail: (err) => {
        Toast.hide()
        reject(err)
      }
    })
  })
},

/**
 * 预览商品图片
 */
previewProductImage() {
  if (!this.data.productImage) return
  wx.previewImage({
    urls: [`${apiBaseUrl}${this.data.productImage}`],
    current: `${apiBaseUrl}${this.data.productImage}`
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
        this.setData({ productImage: '' })
        Toast.quick('已删除')
      }
    }
  })
},

/**
 * 扫描条形码
 */
async scanBarcode() {
  try {
    const res = await wx.scanCode({
      onlyFromCamera: false,
      scanType: ['barCode']
    })

    const barcode = res.result
    if (!barcode) {
      Toast.warning('未识别到条形码')
      return
    }

    this.setData({ barcode })
    Toast.info('正在识别商品...')

    // 查询商品信息
    await this.queryBarcodeInfo(barcode)
  } catch (error) {
    if (error.errMsg && error.errMsg.includes('cancel')) return
    console.error('扫码失败:', error)
    Toast.error('扫码失败')
  }
},

/**
 * 查询条形码商品信息
 */
async queryBarcodeInfo(barcode) {
  try {
    const data = await request({
      url: `/barcode/query?code=${barcode}`,
      method: 'GET'
    })

    if (data.found) {
      this.setData({
        name: data.name || this.data.name,
        barcode: data.barcode,
        productImage: data.image || this.data.productImage
      })
      Toast.success('识别成功')
    } else {
      Toast.info('未找到商品信息，请手动填写')
    }
  } catch (error) {
    console.error('查询商品信息失败:', error)
    Toast.warning('查询失败')
  }
}
```

**2. pages/add/add.wxml**

在合适位置添加：

```xml
<!-- 商品图片 -->
<view class="form-item">
  <view class="label">
    商品图片
    <text class="optional">（选填）</text>
  </view>
  
  <view class="image-upload">
    <view wx:if="{{productImage}}" class="image-preview" bindtap="previewProductImage">
      <image src="{{apiBaseUrl}}{{productImage}}" mode="aspectFill" />
      <view class="image-delete" catchtap="deleteProductImage">
        <text>×</text>
      </view>
    </view>
    
    <view wx:else class="image-upload-btn" bindtap="chooseProductImage">
      <text class="icon">📷</text>
      <text class="text">添加图片</text>
    </view>
  </view>
</view>

<!-- 条形码 -->
<view class="form-item">
  <view class="label">
    条形码
    <text class="optional">（选填）</text>
  </view>
  
  <view class="barcode-input">
    <input 
      type="text" 
      placeholder="扫一扫或手动输入" 
      value="{{barcode}}"
      bindinput="onBarcodeInput"
    />
    <button class="scan-btn" bindtap="scanBarcode" size="mini">
      扫一扫
    </button>
  </view>
</view>
```

**3. pages/add/add.wxss**

添加样式：

```css
/* 图片上传 */
.image-upload {
  margin-top: 20rpx;
}

.image-preview {
  position: relative;
  width: 200rpx;
  height: 200rpx;
  border-radius: 12rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.1);
}

.image-preview image {
  width: 100%;
  height: 100%;
}

.image-delete {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  width: 48rpx;
  height: 48rpx;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 36rpx;
  font-weight: bold;
}

.image-upload-btn {
  width: 200rpx;
  height: 200rpx;
  border: 2rpx dashed #ddd;
  border-radius: 12rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f8f8f8;
}

.image-upload-btn .icon {
  font-size: 60rpx;
  margin-bottom: 12rpx;
}

.image-upload-btn .text {
  font-size: 24rpx;
  color: #999;
}

/* 条形码输入 */
.barcode-input {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 20rpx;
}

.barcode-input input {
  flex: 1;
  padding: 20rpx;
  background: #f8f8f8;
  border-radius: 8rpx;
}

.scan-btn {
  background: #07c160;
  color: white;
  border: none;
  border-radius: 8rpx;
  padding: 20rpx 30rpx;
  font-size: 28rpx;
}
```

**4. 同样修改 pages/edit/edit.js、edit.wxml、edit.wxss**

复制上面的代码到编辑页面。

---

## 🔄 全局Toast替换指南

在所有页面替换 `wx.showToast` 为 `Toast` 工具类：

### app.js

```javascript
// 在文件顶部添加
const { Toast } = require('./utils/toast')

// 替换所有 wx.showToast
// 第46行
Toast.error('登录失败')

// 第65行
Toast.error('登录失败：未获取到 openid')

// 第70行
Toast.error(errorMsg)

// 第75行
Toast.error('网络异常')

// 第118-122行
Toast.info(message)  // 过期提示（如果保留的话）

// 第382行
Toast.success('创建成功')

// 第386行
Toast.error('创建失败')

// 第397行
Toast.warning('请输入邀请码')

// 第414行
Toast.success('已加入团队')

// 第418行
Toast.error('加入失败')

// ... 以此类推
```

### pages/index/index.js

```javascript
const { Toast } = require('../../utils/toast')

// 第90行
Toast.error('登录失败，请稍后重试')

// 第127行
Toast.error('加载失败')

// 第156行
Toast.quick('已刷新')

// 第237行
Toast.info('已标为不提醒')

// 第270行
Toast.quick('已删除')

// 第274行
Toast.error('删除失败')

// ... 更多替换
```

### 快速批量替换脚本

创建 `replace_toast.sh`（可选的批量替换脚本）：

```bash
#!/bin/bash
# 批量替换Toast调用
# 使用前请先备份代码！

# 替换简单成功提示
find pages -name "*.js" -exec sed -i '' 's/wx\.showToast({ title: '\''.*成功'\'', icon: '\''success'\'' })/Toast.success('\''操作成功'\'')/g' {} \;

# 注意：这只是示例，实际需要根据具体情况手动替换
```

**建议**：手动逐个文件替换，确保语义正确。

---

## 🎯 测试验证

### 测试Toast

创建测试页面或在现有页面添加测试按钮：

```javascript
testToast() {
  const tests = [
    { method: 'quick', text: '快速反馈（1.5秒）' },
    { method: 'success', text: '成功提示（2秒）' },
    { method: 'error', text: '错误提示（3秒）' },
    { method: 'warning', text: '警告提示（3秒）' },
    { method: 'info', text: '信息提示（2.5秒）' }
  ]

  let index = 0
  const show = () => {
    if (index < tests.length) {
      const test = tests[index]
      Toast[test.method](test.text)
      index++
      setTimeout(show, 3500)  // 等待上一个消失
    }
  }

  show()
}
```

### 测试图片上传

1. 进入添加商品页面
2. 点击"添加图片"按钮
3. 选择一张图片
4. 观察：
   - 显示"正在上传..."
   - 上传完成显示"上传成功"（2秒）
   - 图片显示在页面上

### 测试条形码扫描

1. 进入添加商品页面
2. 点击"扫一扫"按钮
3. 扫描一个商品条形码（可以用相册中的条形码图片）
4. 观察：
   - 显示"正在识别商品..."（2.5秒）
   - 识别成功显示"识别成功"（2秒）
   - 商品名称和图片自动填充

---

## 📊 预期效果对比

### Toast提示时间

| 场景 | 旧版本 | 新版本 | 改进 |
|-----|-------|--------|------|
| 简单操作 | 1.5秒（默认） | 1.5秒（明确） | ✅ 标准化 |
| 成功提示 | 1.5秒 | 2秒 | ✅ 时间更充裕 |
| 错误提示 | 1.5秒 | 3秒 | ✅ 看得更清楚 |
| 警告提示 | 1.5秒 | 3秒 | ✅ 有时间反应 |

### 用户体验

**旧版本问题**：
- ❌ Toast 太快看不清
- ❌ 每次进入首页都提示过期
- ❌ 无法上传商品图片
- ❌ 手动输入商品信息繁琐

**新版本改进**：
- ✅ Toast 时间合理，易读
- ✅ 安静的过期数量显示
- ✅ 支持图片上传和预览
- ✅ 扫码自动识别商品

---

## ⚠️ 注意事项

### 1. 图片上传权限

在 `app.json` 中配置域名（如果还没有）：

```json
{
  "permission": {
    "scope.writePhotosAlbum": {
      "desc": "保存商品图片到相册"
    }
  }
}
```

### 2. 服务器域名配置

在微信小程序后台配置合法域名：

- **request合法域名**：`https://dhlhy.cn`
- **uploadFile合法域名**：`https://dhlhy.cn`
- **downloadFile合法域名**：`https://dhlhy.cn`

### 3. 开发调试

开发阶段，在微信开发者工具中：
- 详情 → 本地设置 → 勾选"不校验合法域名"
- 可以使用 HTTP 和 localhost

### 4. 图片存储

生产环境建议：
- 定期清理无用图片
- 配置 CDN 加速
- 长期建议迁移到阿里云OSS或腾讯云COS

---

## 🎯 实施优先级

### 高优先级（建议立即实施）

1. ✅ Toast 优化 - 提升用户体验
2. ✅ 去掉过期提示 - 减少打扰

### 中优先级（本周完成）

3. ✅ 图片上传 - 功能增强

### 低优先级（按需实施）

4. ✅ 条形码识别 - 便捷功能（需要API服务）

---

## 📚 相关文档

- [MINIPROGRAM_IMPROVEMENTS.md](MINIPROGRAM_IMPROVEMENTS.md) - 详细技术方案
- [API_RESPONSE_FORMAT.md](API_RESPONSE_FORMAT.md) - API响应格式
- [UPDATE_SUMMARY.md](UPDATE_SUMMARY.md) - 更新总结

---

**所有代码和文档已准备就绪，按照本指南即可完成实施！** 🚀
