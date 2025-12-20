#!/bin/bash
# 衣柜模块部署脚本

echo "🚀 开始部署衣柜管理模块..."
echo ""

# 1. 更新后端代码
echo "📥 1. 更新后端代码..."
cd /srv/app/display_date_python
git pull

# 2. 执行数据库迁移
echo ""
echo "🗄️ 2. 执行数据库迁移..."
mysql -u root -p <<'EOF'
USE display_date;

-- 1. 衣服分类/标签表
CREATE TABLE IF NOT EXISTS wardrobe_categories (
    id VARCHAR(36) PRIMARY KEY,
    owner_openid VARCHAR(128) NOT NULL,
    name VARCHAR(50) NOT NULL COMMENT '标签名称，如T恤、短袖、外套',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_owner (owner_openid),
    UNIQUE KEY uk_owner_name (owner_openid, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='衣服分类标签';

-- 2. 衣服物品表
CREATE TABLE IF NOT EXISTS wardrobe_items (
    id VARCHAR(36) PRIMARY KEY,
    owner_openid VARCHAR(128) NOT NULL,
    category_id VARCHAR(36) NOT NULL COMMENT '分类ID',
    name VARCHAR(100) NOT NULL COMMENT '衣服名称',
    color VARCHAR(50) DEFAULT NULL COMMENT '颜色',
    size VARCHAR(20) DEFAULT NULL COMMENT '尺码',
    season VARCHAR(20) DEFAULT NULL COMMENT '季节：春、夏、秋、冬',
    brand VARCHAR(100) DEFAULT NULL COMMENT '品牌',
    price DECIMAL(10,2) DEFAULT NULL COMMENT '价格',
    purchase_date DATE DEFAULT NULL COMMENT '购买日期',
    image_url VARCHAR(1024) DEFAULT NULL COMMENT '衣服图片',
    note TEXT DEFAULT NULL COMMENT '备注',
    deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_owner (owner_openid),
    INDEX idx_category (category_id),
    INDEX idx_deleted (deleted),
    FOREIGN KEY (category_id) REFERENCES wardrobe_categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='衣服物品';

-- 3. 虚拟试衣搭配表
CREATE TABLE IF NOT EXISTS wardrobe_outfits (
    id VARCHAR(36) PRIMARY KEY,
    owner_openid VARCHAR(128) NOT NULL,
    name VARCHAR(100) NOT NULL COMMENT '搭配名称',
    items JSON NOT NULL COMMENT '衣服ID数组',
    occasion VARCHAR(50) DEFAULT NULL COMMENT '场合：休闲、正式、运动等',
    season VARCHAR(20) DEFAULT NULL COMMENT '季节',
    image_url VARCHAR(1024) DEFAULT NULL COMMENT '搭配截图',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_owner (owner_openid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='虚拟试衣搭配方案';

EOF

# 3. 清理缓存
echo ""
echo "🗑️ 3. 清理Python缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete

# 4. 重启服务
echo ""
echo "🔄 4. 重启后端服务..."
systemctl restart display-date

# 5. 等待启动
echo ""
echo "⏳ 5. 等待服务启动（3秒）..."
sleep 3

# 6. 检查状态
echo ""
echo "✅ 6. 检查服务状态..."
systemctl status display-date --no-pager -l | head -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 后端部署完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 前端部署步骤："
echo "  1. 微信开发者工具中拉取最新代码"
echo "  2. 清除缓存并重新编译"
echo "  3. 在底部导航应该能看到【穿】按钮"
echo ""
echo "🧪 测试功能："
echo "  1. 点击【穿】进入衣柜管理"
echo "  2. 添加标签（如：T恤、外套）"
echo "  3. 点击标签进入，添加衣服"
echo "  4. 返回首页查看统计数字"
echo "  5. 点击【虚拟试衣】测试搭配功能"
echo ""
echo "🔗 API端点："
echo "  GET  /wardrobe/categories       - 获取分类列表"
echo "  POST /wardrobe/categories       - 创建分类"
echo "  GET  /wardrobe/items            - 获取衣服列表"
echo "  POST /wardrobe/items            - 创建衣服"
echo "  GET  /wardrobe/outfits          - 获取搭配方案"
echo "  POST /wardrobe/outfits          - 创建搭配"
echo ""
