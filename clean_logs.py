#!/usr/bin/env python3
"""
独立的日志清理工具

可以手动运行或通过 cron 定期执行
使用方法: python3 clean_logs.py
"""

import sys
from pathlib import Path

# 添加项目路径到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.logger import log_manager

if __name__ == "__main__":
    print("开始清理日志...")
    print(f"日志目录: {log_manager.log_dir}")
    print(f"保留天数: {log_manager.keep_days}")
    print(f"最大总大小: {log_manager.max_total_size_bytes / (1024**3):.2f} GB")
    print()
    
    log_manager.cleanup()
    
    print("\n日志清理工具执行完毕")
