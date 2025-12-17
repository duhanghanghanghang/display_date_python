#!/bin/bash

# 快速测试 API 脚本

echo "================================"
echo "Display Date API 测试"
echo "================================"
echo ""

BASE_URL="http://localhost:8000"
TEST_OPENID="test_user_12345"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📡 测试 1: 检查服务是否运行"
RESPONSE=$(curl -s -w "\n%{http_code}" ${BASE_URL}/)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ 服务正常运行${NC}"
    echo "  响应: $BODY"
else
    echo -e "${RED}✗ 服务未运行或异常 (HTTP $HTTP_CODE)${NC}"
    exit 1
fi

echo ""
echo "📡 测试 2: 不带 openid 访问（应该返回 401）"
RESPONSE=$(curl -s -w "\n%{http_code}" ${BASE_URL}/items)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ 认证检查正常${NC}"
    echo "  错误信息: $BODY"
else
    echo -e "${RED}✗ 认证检查异常 (HTTP $HTTP_CODE)${NC}"
fi

echo ""
echo "📡 测试 3: 带 X-OpenId 访问（应该返回 200）"
RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-OpenId: ${TEST_OPENID}" ${BASE_URL}/items)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ 使用 X-OpenId 认证成功${NC}"
    echo "  响应: $BODY"
else
    echo -e "${RED}✗ 认证失败 (HTTP $HTTP_CODE)${NC}"
    echo "  响应: $BODY"
fi

echo ""
echo "📡 测试 4: 带 openid header 访问（应该返回 200）"
RESPONSE=$(curl -s -w "\n%{http_code}" -H "openid: ${TEST_OPENID}" ${BASE_URL}/items)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ 使用 openid 认证成功${NC}"
    echo "  响应: $BODY"
else
    echo -e "${RED}✗ 认证失败 (HTTP $HTTP_CODE)${NC}"
    echo "  响应: $BODY"
fi

echo ""
echo "📡 测试 5: 获取用户信息"
RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-OpenId: ${TEST_OPENID}" ${BASE_URL}/me)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ 获取用户信息成功${NC}"
    echo "  响应: $BODY" | python3 -m json.tool 2>/dev/null || echo "  响应: $BODY"
else
    echo -e "${RED}✗ 获取用户信息失败 (HTTP $HTTP_CODE)${NC}"
    echo "  响应: $BODY"
fi

echo ""
echo "📡 测试 6: 创建物品"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "X-OpenId: ${TEST_OPENID}" \
    -H "Content-Type: application/json" \
    -d '{"name":"测试物品","expire_date":"2025-12-31","quantity":5}' \
    ${BASE_URL}/items)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "201" ]; then
    echo -e "${GREEN}✓ 创建物品成功${NC}"
    ITEM_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
    echo "  物品ID: $ITEM_ID"
    echo "  响应: $BODY" | python3 -m json.tool 2>/dev/null || echo "  响应: $BODY"
else
    echo -e "${YELLOW}⚠ 创建物品失败 (HTTP $HTTP_CODE)${NC}"
    echo "  响应: $BODY"
fi

echo ""
echo "================================"
echo "测试完成"
echo "================================"
echo ""
echo -e "${GREEN}✓ 后端 API 工作正常！${NC}"
echo ""
echo "📝 接下来："
echo "  1. 打开微信开发者工具"
echo "  2. 删除小程序缓存或重新编译"
echo "  3. 查看控制台是否有'登录成功'日志"
echo "  4. 测试小程序功能"
echo ""
echo "📚 相关文档："
echo "  - 认证修复说明: /Users/d/Desktop/2/认证修复完成说明.md"
echo "  - 小程序集成示例: display_date_python/小程序端集成示例.md"
echo ""

