#!/usr/bin/env python3
"""
测试新功能的脚本
验证日志系统和 webhook 路由是否正常工作
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("测试新功能")
print("=" * 60)
print()

# 测试 1: 日志系统
print("测试 1: 日志系统")
print("-" * 60)
try:
    from app.logger import logger, log_manager
    
    logger.info("这是一条测试信息日志")
    logger.warning("这是一条测试警告日志")
    logger.error("这是一条测试错误日志")
    
    print("✅ 日志系统初始化成功")
    print(f"   日志目录: {log_manager.log_dir}")
    print(f"   保留天数: {log_manager.keep_days}")
    print(f"   最大大小: {log_manager.max_total_size_bytes / (1024**3):.2f} GB")
    
    # 检查日志文件是否创建
    log_files = list(log_manager.log_dir.glob("*.log*"))
    print(f"   日志文件: {len(log_files)} 个")
    for f in log_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"     - {f.name} ({size_mb:.2f} MB)")
except Exception as e:
    print(f"❌ 日志系统测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试 2: 中间件
print("测试 2: 中间件")
print("-" * 60)
try:
    from app.middleware import LoggingMiddleware
    print("✅ 日志中间件导入成功")
except Exception as e:
    print(f"❌ 中间件导入失败: {e}")

print()

# 测试 3: Webhook 路由
print("测试 3: Webhook 路由")
print("-" * 60)
try:
    from app.routers import webhook
    print("✅ Webhook 路由导入成功")
    print(f"   路由前缀: {webhook.router.prefix}")
    print(f"   标签: {webhook.router.tags}")
except Exception as e:
    print(f"❌ Webhook 路由导入失败: {e}")

print()

# 测试 4: 主应用
print("测试 4: 主应用集成")
print("-" * 60)
try:
    from app.main import app
    
    # 获取所有路由
    routes = [r.path for r in app.routes if hasattr(r, 'path')]
    
    print("✅ 应用导入成功")
    print(f"   总路由数: {len(routes)}")
    
    # 检查 webhook 路由
    webhook_routes = [r for r in routes if r.startswith('/webhook')]
    if webhook_routes:
        print(f"   Webhook 路由: ✅")
        for route in webhook_routes:
            print(f"     - {route}")
    else:
        print(f"   Webhook 路由: ❌ 未找到")
    
    # 检查其他重要路由
    important_routes = ['/login', '/items', '/teams']
    for route_prefix in important_routes:
        matching = [r for r in routes if r.startswith(route_prefix)]
        if matching:
            print(f"   {route_prefix}: ✅")
        else:
            print(f"   {route_prefix}: ❌")
            
except Exception as e:
    print(f"❌ 应用导入失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试 5: 配置
print("测试 5: 配置")
print("-" * 60)
try:
    from app.config import settings
    
    print("✅ 配置加载成功")
    print(f"   数据库 URL: {settings.database_url[:30]}...")
    
    if hasattr(settings, 'github_webhook_secret'):
        if settings.github_webhook_secret:
            print(f"   Webhook 密钥: 已配置 ✅")
        else:
            print(f"   Webhook 密钥: 未配置 ⚠️  (自动部署功能需要)")
    else:
        print(f"   Webhook 密钥: 配置项不存在 ❌")
        
except Exception as e:
    print(f"❌ 配置加载失败: {e}")

print()

# 测试 6: 部署脚本
print("测试 6: 部署脚本")
print("-" * 60)
auto_deploy_script = project_root / "auto_deploy.sh"
clean_logs_script = project_root / "clean_logs.py"

if auto_deploy_script.exists():
    import stat
    is_executable = auto_deploy_script.stat().st_mode & stat.S_IXUSR
    print(f"✅ auto_deploy.sh 存在")
    print(f"   可执行: {'是 ✅' if is_executable else '否 ❌'}")
else:
    print(f"❌ auto_deploy.sh 不存在")

if clean_logs_script.exists():
    print(f"✅ clean_logs.py 存在")
else:
    print(f"❌ clean_logs.py 不存在")

print()

# 总结
print("=" * 60)
print("测试完成！")
print("=" * 60)
print()
print("下一步操作：")
print("1. 启动应用: python3 run.py")
print("2. 查看日志: tail -f logs/display_date.log")
print("3. 测试 API: curl http://localhost:8000/webhook/test")
print("4. 配置 webhook: 查看 WEBHOOK_SETUP.md")
print()
