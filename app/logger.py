"""
日志管理模块
- 单独的日志文件夹
- 按天分割日志文件
- 自动保留一周的日志
- 控制日志总大小不超过2G
"""
import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
import os


class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs", max_total_size_gb: float = 2.0, keep_days: int = 7):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志文件夹路径
            max_total_size_gb: 日志文件夹最大总大小（GB）
            keep_days: 保留日志天数
        """
        self.log_dir = Path(log_dir)
        self.max_total_size_bytes = int(max_total_size_gb * 1024 * 1024 * 1024)
        self.keep_days = keep_days
        
        # 创建日志目录
        self.log_dir.mkdir(exist_ok=True)
        
    def get_log_files(self) -> list[tuple[Path, float]]:
        """
        获取所有日志文件及其大小
        
        Returns:
            [(文件路径, 修改时间), ...] 按修改时间排序
        """
        log_files = []
        for file in self.log_dir.glob("*.log*"):
            if file.is_file():
                stat = file.stat()
                log_files.append((file, stat.st_mtime))
        
        # 按修改时间排序（最旧的在前）
        log_files.sort(key=lambda x: x[1])
        return log_files
    
    def get_total_size(self) -> int:
        """获取日志文件夹总大小（字节）"""
        total_size = 0
        for file, _ in self.get_log_files():
            total_size += file.stat().st_size
        return total_size
    
    def clean_old_logs(self):
        """清理旧日志"""
        now = datetime.now()
        cutoff_time = now - timedelta(days=self.keep_days)
        cutoff_timestamp = cutoff_time.timestamp()
        
        deleted_count = 0
        for file, mtime in self.get_log_files():
            if mtime < cutoff_timestamp:
                try:
                    file.unlink()
                    deleted_count += 1
                    print(f"删除过期日志: {file.name}")
                except Exception as e:
                    print(f"删除日志文件失败 {file.name}: {e}")
        
        if deleted_count > 0:
            print(f"共删除 {deleted_count} 个过期日志文件")
    
    def clean_by_size(self):
        """根据大小清理日志，确保总大小不超过限制"""
        total_size = self.get_total_size()
        
        if total_size <= self.max_total_size_bytes:
            print(f"日志总大小: {total_size / (1024**3):.2f} GB (未超限)")
            return
        
        print(f"日志总大小 {total_size / (1024**3):.2f} GB 超过限制 {self.max_total_size_bytes / (1024**3):.2f} GB")
        print("开始清理最旧的日志文件...")
        
        log_files = self.get_log_files()
        deleted_count = 0
        
        for file, _ in log_files:
            if total_size <= self.max_total_size_bytes:
                break
            
            try:
                file_size = file.stat().st_size
                file.unlink()
                total_size -= file_size
                deleted_count += 1
                print(f"删除日志: {file.name} (释放 {file_size / (1024**2):.2f} MB)")
            except Exception as e:
                print(f"删除日志文件失败 {file.name}: {e}")
        
        print(f"清理完成，删除 {deleted_count} 个文件")
        print(f"当前日志总大小: {total_size / (1024**3):.2f} GB")
    
    def cleanup(self):
        """执行完整的清理流程"""
        print("\n" + "="*50)
        print("开始日志清理")
        print("="*50)
        
        # 1. 先删除过期日志
        self.clean_old_logs()
        
        # 2. 检查并按大小清理
        self.clean_by_size()
        
        print("="*50)
        print("日志清理完成\n")


def setup_logger(name: str = "display_date", log_dir: str = "logs") -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_dir: 日志文件夹路径
        
    Returns:
        配置好的日志记录器
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 如果已经有处理器，不重复添加
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器 - 按天分割，保留备份
    file_handler = TimedRotatingFileHandler(
        filename=log_path / f"{name}.log",
        when='midnight',  # 每天午夜分割
        interval=1,  # 每1天
        backupCount=7,  # 保留7天
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"  # 备份文件后缀
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 创建全局日志管理器和日志记录器
log_manager = LogManager(log_dir="logs", max_total_size_gb=2.0, keep_days=7)
logger = setup_logger()
