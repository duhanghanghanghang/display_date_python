# 部署错误修复说明

## 🐛 发现的问题

### 错误日志

```
2025-12-19 16:19:44 - ERROR - 部署过程中发生错误: [Errno 2] No such file or directory: 'bash'
FileNotFoundError: [Errno 2] No such file or directory: 'bash'
```

### 根本原因

在 `app/routers/webhook.py` 中，使用了相对命令 `bash`：

```python
# ❌ 错误的代码
result = subprocess.run(
    ["bash", str(deploy_script)],  # 找不到 'bash'
    ...
)
```

**问题分析**：
- Python 的 `subprocess.run()` 不会使用 shell 的 PATH 环境变量
- 直接传递命令列表时，需要提供可执行文件的完整路径
- 不同系统中 `bash` 的位置可能不同

---

## ✅ 解决方案

### 修复代码

```python
# ✅ 正确的代码
result = subprocess.run(
    ["/bin/bash", str(deploy_script)],  # 使用完整路径
    cwd=str(project_root),
    capture_output=True,
    text=True,
    timeout=300
)
```

### 为什么使用 `/bin/bash`？

1. **标准位置**：在几乎所有 Unix/Linux 系统中，`bash` 都位于 `/bin/bash`
2. **可靠性**：不依赖 PATH 环境变量
3. **兼容性**：适用于服务器环境（systemd、cron等）

---

## 🚀 应用修复

### 方式1：推送代码（推荐）

```bash
cd /Users/d/Desktop/2/display_date_python

# 添加修复
git add app/routers/webhook.py

# 提交
git commit -m "修复部署脚本执行路径问题"

# 推送
git push origin master
```

**注意**：此次推送后，webhook 会尝试执行部署，但可能仍会失败一次（因为服务器上还是旧代码）。没关系，部署完成后，下次推送就正常了。

### 方式2：服务器手动修复

```bash
# SSH 连接到服务器
ssh user@your-server

# 进入项目目录
cd /srv/app/display_date_python

# 拉取最新代码
git pull origin master

# 重启服务
sudo systemctl restart display-date

# 查看状态
sudo systemctl status display-date
```

---

## 🧪 测试修复

### 1. 推送测试代码

```bash
# 创建空提交测试
git commit --allow-empty -m "测试webhook自动部署"
git push
```

### 2. 查看服务器日志

```bash
# 实时查看日志
tail -f /path/to/logs/display_date.log

# 或者通过 SSH
ssh user@server "tail -f /srv/app/display_date_python/logs/display_date.log"
```

### 3. 预期日志输出

成功的部署日志应该类似：

```
2025-12-19 16:30:00 - INFO - 收到 GitHub webhook 事件: push
2025-12-19 16:30:00 - INFO - 已将部署任务加入后台队列
2025-12-19 16:30:01 - INFO - 开始执行自动部署...
2025-12-19 16:30:02 - INFO - 部署输出:
======================================
开始自动部署
======================================
步骤 1/5: 拉取最新代码
--------------------------------------
当前分支: master
拉取最新代码...
✓ 代码拉取成功
步骤 2/5: 更新依赖
--------------------------------------
...
2025-12-19 16:30:30 - INFO - 自动部署成功完成
```

---

## 🔍 其他可能的问题

### 问题1：脚本没有执行权限

**错误**：
```
Permission denied
```

**解决**：
```bash
chmod +x auto_deploy.sh
```

### 问题2：脚本路径不存在

**错误**：
```
部署脚本不存在: /path/to/auto_deploy.sh
```

**解决**：
```bash
# 确认脚本位置
ls -la auto_deploy.sh

# 如果不存在，检查项目根目录
pwd
ls -la
```

### 问题3：Git 权限问题

**错误**：
```
Permission denied (publickey)
```

**解决**：
```bash
# 检查 SSH 密钥
ssh -T git@github.com

# 或使用 HTTPS
git remote set-url origin https://github.com/user/repo.git
```

### 问题4：虚拟环境问题

**错误**：
```
venv/bin/python: No such file or directory
```

**解决**：
```bash
# 重新创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 验证清单

部署成功后，验证以下内容：

- [ ] GitHub webhook 显示绿色 ✓
- [ ] 服务器日志显示"自动部署成功完成"
- [ ] `git log` 显示最新提交
- [ ] 服务正常运行（`systemctl status display-date`）
- [ ] API 接口正常响应
- [ ] 数据库迁移已执行（如有）

---

## 🎯 最佳实践

### 1. 使用完整路径

```python
# ✅ 好的做法
subprocess.run(["/bin/bash", script])
subprocess.run(["/usr/bin/python3", script])
subprocess.run(["/usr/bin/git", "pull"])

# ❌ 避免使用
subprocess.run(["bash", script])
subprocess.run(["python3", script])
```

### 2. 设置工作目录

```python
subprocess.run(
    ["/bin/bash", script],
    cwd=project_root,  # 设置工作目录
    ...
)
```

### 3. 捕获输出

```python
result = subprocess.run(
    ["/bin/bash", script],
    capture_output=True,  # 捕获 stdout 和 stderr
    text=True,            # 以文本模式返回
    ...
)

logger.info(f"输出: {result.stdout}")
if result.stderr:
    logger.warning(f"错误: {result.stderr}")
```

### 4. 超时保护

```python
try:
    result = subprocess.run(
        [...],
        timeout=300  # 5分钟超时
    )
except subprocess.TimeoutExpired:
    logger.error("部署超时")
```

---

## 📚 相关文档

- [WEBHOOK_FIX.md](WEBHOOK_FIX.md) - Webhook 完整修复指南
- [QUICK_FIX_COMMANDS.md](QUICK_FIX_COMMANDS.md) - 快速修复命令
- [UPDATE_SUMMARY.md](UPDATE_SUMMARY.md) - 更新总结

---

## ✅ 修复完成

执行以下命令应用修复：

```bash
cd /Users/d/Desktop/2/display_date_python
git add .
git commit -m "修复webhook部署脚本执行路径问题"
git push
```

等待服务器自动部署完成（约1分钟），然后推送一个测试提交验证。

---

**修复后，自动部署应该可以正常工作了！** 🎉

如果仍有问题，查看完整日志：
```bash
tail -100 logs/display_date.log | grep -E "(webhook|部署|ERROR)"
```
