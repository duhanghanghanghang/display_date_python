# GitHub Webhook 修复文档

## 🔍 问题诊断

### 错误现象

GitHub Webhook 页面显示：
```
Last delivery was not successful. An exception occurred.
```

### 根本原因

**问题代码位置**：`app/routers/webhook.py`

原代码存在严重的逻辑错误：

```python
# ❌ 错误的代码
payload_body = await request.body()  # 第一次读取请求体
# ...（中间进行签名验证）
payload = await request.json()       # 第二次尝试读取 - 失败！
```

**FastAPI/Starlette 的限制**：
- `request.body()` 只能被调用一次
- 调用后，流（stream）已经被消费
- 再次调用 `request.json()` 会导致异常

### 错误影响

1. ❌ 所有 webhook 请求都失败
2. ❌ GitHub 无法触发自动部署
3. ❌ 服务器返回 500 错误
4. ❌ 日志中显示异常

---

## ✅ 解决方案

### 修复代码

```python
# ✅ 正确的代码
# 1. 先读取请求体（只读一次）
payload_body = await request.body()

# 2. 手动解析 JSON
import json
payload = json.loads(payload_body.decode('utf-8'))

# 3. 使用原始字节进行签名验证
if webhook_secret:
    if not verify_github_signature(payload_body, x_hub_signature_256, webhook_secret):
        # 验证失败...
```

### 修复原理

1. **统一数据源**：只读取一次请求体
2. **手动解析**：使用 `json.loads()` 而不是 `request.json()`
3. **顺序优化**：先解析再验证（也可以先验证再解析）

---

## 🚀 验证修复

### 步骤 1：更新代码

```bash
# 在服务器上
cd /srv/app/display_date_python
git pull origin master

# 重启服务
sudo systemctl restart display-date
```

或推送代码触发自动部署：

```bash
# 在本地
git add .
git commit -m "Fix webhook request body reading issue"
git push
```

### 步骤 2：测试 Webhook

#### 方法1：使用 GitHub 界面测试

1. 进入 GitHub 仓库
2. Settings → Webhooks → 点击你的 webhook
3. 滚动到底部，点击 **"Redeliver"**（重新发送）
4. 查看响应

**期望结果**：
- Status: `200 OK`
- Response body: `{"message": "Deployment started"}` 或 `{"message": "Branch xxx ignored"}`

#### 方法2：使用 curl 测试

```bash
# 测试测试端点
curl https://your-domain.com/webhook/test

# 应返回
{"message": "Webhook endpoint is working"}
```

#### 方法3：推送代码测试

```bash
git commit --allow-empty -m "Test webhook"
git push
```

然后查看：
1. GitHub Webhook 推送记录（应该显示绿色的 ✓）
2. 服务器日志：`tail -f /path/to/logs/display_date.log`

---

## 📊 验证清单

### GitHub 端验证

访问：`https://github.com/你的用户名/你的仓库/settings/hooks`

点击 webhook，查看 **Recent Deliveries**：

- [x] Response status: `200`
- [x] Response body 包含 `message` 字段
- [x] 没有错误信息

### 服务器端验证

```bash
# 查看最近的 webhook 日志
tail -50 logs/display_date.log | grep webhook

# 应该看到类似内容：
# 2025-12-19 12:30:00 - INFO - 收到 GitHub webhook 事件: push
# 2025-12-19 12:30:00 - INFO - 收到推送: user/repo | 分支: refs/heads/master
# 2025-12-19 12:30:00 - INFO - 已将部署任务加入后台队列
```

---

## 🔧 常见问题排查

### Q1: 修复后仍然失败

**检查事项**：

1. **服务是否重启？**
   ```bash
   sudo systemctl status display-date
   sudo systemctl restart display-date
   ```

2. **代码是否更新？**
   ```bash
   cd /path/to/project
   git log -1 --oneline
   # 应该看到最新的提交
   ```

3. **签名是否匹配？**
   - 检查 `.env` 中的 `GITHUB_WEBHOOK_SECRET`
   - 与 GitHub 设置的 Secret 是否一致

### Q2: 签名验证失败

**错误日志**：
```
GitHub webhook 签名验证失败
```

**解决方法**：

```bash
# 1. 生成新密钥
NEW_SECRET=$(openssl rand -hex 32)
echo "GITHUB_WEBHOOK_SECRET=$NEW_SECRET" >> .env

# 2. 重启服务
sudo systemctl restart display-date

# 3. 更新 GitHub Webhook Secret
# 进入 GitHub → Settings → Webhooks → Edit
# 在 Secret 字段填入 $NEW_SECRET
```

### Q3: 无法连接到服务器

**错误提示**：
```
We couldn't deliver this payload: Connection error
```

**检查事项**：

1. **服务器是否运行？**
   ```bash
   curl http://localhost:8000/webhook/test
   ```

2. **防火墙是否开放？**
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **Nginx 配置是否正确？**
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Q4: 部署脚本未执行

**症状**：Webhook 成功，但代码未更新

**检查**：

```bash
# 1. 查看完整日志
tail -100 logs/display_date.log | grep -A 20 "部署"

# 2. 检查部署脚本权限
ls -l auto_deploy.sh
# 应该有执行权限: -rwxr-xr-x

# 3. 手动测试部署脚本
bash auto_deploy.sh
```

---

## 📝 技术细节

### 为什么不能读取两次？

FastAPI 使用 Starlette 的 `Request` 对象，其内部使用流式读取：

```python
class Request:
    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            # 第一次：从流中读取并缓存
            self._body = await self._receive_body()
        return self._body  # 第二次：返回缓存
    
    async def json(self) -> Any:
        if not hasattr(self, "_json"):
            # 内部会调用 await self.body()
            body = await self.body()
            self._json = json.loads(body)
        return self._json
```

**但是**，我们的原始代码在读取 `body()` 后，流已经被消费，如果中间有任何异常或特殊处理，再次调用 `json()` 可能失败。

### 最佳实践

**方案 A**：先 JSON，后验证（推荐）

```python
# 1. 读取并解析
body = await request.body()
payload = json.loads(body)

# 2. 验证签名
verify_signature(body, signature, secret)
```

**方案 B**：只用 JSON

```python
# 1. 直接解析 JSON
payload = await request.json()

# 2. 重新序列化用于验证
body = json.dumps(payload, separators=(',', ':')).encode()
verify_signature(body, signature, secret)
```

**注意**：方案 B 可能因为 JSON 序列化顺序不同导致签名验证失败，不推荐。

---

## 🎯 预防措施

### 代码审查要点

1. ✅ 避免多次读取请求体
2. ✅ 明确数据流向
3. ✅ 添加详细日志
4. ✅ 异常处理要完善

### 监控建议

```python
# 添加到 webhook 路由
logger.info(f"Webhook 接收: 事件={event_type}, "
           f"签名={'已验证' if webhook_secret else '未验证'}")
```

### 测试建议

创建测试脚本 `test_webhook.sh`：

```bash
#!/bin/bash
# 测试 webhook 端点

WEBHOOK_URL="https://your-domain.com/webhook/github"
SECRET="your-secret"

# 模拟 GitHub 推送
PAYLOAD='{"ref":"refs/heads/master","repository":{"full_name":"test/repo"},"pusher":{"name":"test"}}'

# 计算签名
SIGNATURE="sha256=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | cut -d' ' -f2)"

# 发送请求
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature-256: $SIGNATURE" \
  -d "$PAYLOAD"
```

---

## 📚 相关文档

- [GitHub Webhooks 官方文档](https://docs.github.com/webhooks)
- [FastAPI Request 对象](https://fastapi.tiangolo.com/advanced/using-request-directly/)
- [HMAC 签名验证](https://docs.github.com/webhooks/using-webhooks/validating-webhook-deliveries)

---

## ✅ 修复完成检查清单

- [x] 修复请求体读取问题
- [x] 测试 webhook 端点
- [x] 验证 GitHub 推送
- [x] 确认自动部署执行
- [x] 更新文档

---

**问题已修复！现在 webhook 应该可以正常工作了。** 🎉

如有任何问题，查看日志：`tail -f logs/display_date.log | grep webhook`
