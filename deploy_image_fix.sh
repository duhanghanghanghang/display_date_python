#!/bin/bash
# 图片字段保存问题 - 紧急修复部署脚本

echo "🔧 部署图片保存修复..."
echo ""

cd /srv/app/display_date_python || exit 1

echo "📥 1. 拉取最新代码..."
git pull

echo ""
echo "🔄 2. 重启服务..."
systemctl restart display-date

echo ""
echo "⏳ 3. 等待服务启动（3秒）..."
sleep 3

echo ""
echo "✅ 4. 检查服务状态..."
systemctl status display-date --no-pager -l | head -15

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 修复完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 修复内容："
echo "  ✅ PATCH 接口：去掉 by_alias=True"
echo "  ✅ POST 接口：修复恢复已删除记录的逻辑"
echo "  ✅ 字段映射：productImage → product_image"
echo ""
echo "🧪 测试方法："
echo "  1. 在小程序中上传图片并保存"
echo "  2. 刷新列表，应该能看到图片"
echo "  3. 或者运行：curl 'https://dhlhy.cn/items?teamId=' -H 'X-OpenId: xxx'"
echo ""
