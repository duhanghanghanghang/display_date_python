#!/bin/bash
# 图片回显修复 - 快速部署脚本

echo "🔧 开始修复图片回显问题..."

cd /srv/app/display_date_python

echo "📥 1. 拉取最新代码..."
git pull

echo "🔄 2. 重启服务..."
systemctl restart display-date

echo "⏳ 3. 等待服务启动..."
sleep 3

echo "✅ 4. 检查服务状态..."
systemctl status display-date --no-pager -l | head -20

echo ""
echo "🎉 修复完成！"
echo ""
echo "📝 修复内容："
echo "   - 添加了 product_image -> productImage 的字段别名映射"
echo "   - 前端现在可以正确接收并显示图片了"
echo ""
echo "🧪 测试方法："
echo "   1. 在小程序中点击任意有图片的物品"
echo "   2. 进入编辑页面，查看图片是否正常回显"
echo "   3. 返回列表页面，查看图片是否正常显示"
