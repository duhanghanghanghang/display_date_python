"""
Webhook 路由
用于接收 GitHub 推送通知并自动部署
"""
import hashlib
import hmac
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks, status
from ..logger import logger
from ..config import settings
from ..schemas import MessageResponse

router = APIRouter(prefix="/webhook", tags=["webhook"])


def verify_github_signature(payload_body: bytes, signature_header: Optional[str], secret: str) -> bool:
    """
    验证 GitHub webhook 签名
    
    Args:
        payload_body: 请求体字节
        signature_header: GitHub 签名头 (X-Hub-Signature-256)
        secret: Webhook 密钥
        
    Returns:
        是否验证通过
    """
    if not signature_header or not secret:
        return False
    
    # GitHub 签名格式: sha256=<hash>
    hash_algorithm, github_signature = signature_header.split('=', 1)
    
    if hash_algorithm != 'sha256':
        return False
    
    # 计算预期签名
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    # 比较签名
    return hmac.compare_digest(expected_signature, github_signature)


async def run_deployment():
    """
    执行部署脚本
    
    在后台运行部署脚本
    """
    try:
        logger.info("开始执行自动部署...")
        
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        deploy_script = project_root / "auto_deploy.sh"
        
        if not deploy_script.exists():
            logger.error(f"部署脚本不存在: {deploy_script}")
            return
        
        # 执行部署脚本
        result = subprocess.run(
            ["bash", str(deploy_script)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        # 记录输出
        if result.stdout:
            logger.info(f"部署输出:\n{result.stdout}")
        
        if result.stderr:
            logger.warning(f"部署错误输出:\n{result.stderr}")
        
        if result.returncode == 0:
            logger.info("自动部署成功完成")
        else:
            logger.error(f"自动部署失败，退出码: {result.returncode}")
            
    except subprocess.TimeoutExpired:
        logger.error("部署脚本执行超时（超过5分钟）")
    except Exception as e:
        logger.error(f"部署过程中发生错误: {e}", exc_info=True)


@router.post("/github", response_model=MessageResponse)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None),
):
    """
    接收 GitHub Webhook 推送
    
    当代码推送到 GitHub 时，自动拉取并部署最新代码
    """
    # 读取请求体（只能读取一次）
    payload_body = await request.body()
    
    # 先解析 JSON（因为后面还需要用）
    try:
        import json
        payload = json.loads(payload_body.decode('utf-8'))
    except Exception as e:
        logger.error(f"解析 webhook payload 失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # 验证签名（如果配置了密钥）
    webhook_secret = getattr(settings, 'github_webhook_secret', None)
    if webhook_secret:
        if not verify_github_signature(payload_body, x_hub_signature_256, webhook_secret):
            logger.warning("GitHub webhook 签名验证失败")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        logger.info("GitHub webhook 签名验证通过")
    else:
        logger.warning("未配置 webhook 密钥，跳过签名验证")
    
    # 记录事件
    event_type = x_github_event or "unknown"
    logger.info(f"收到 GitHub webhook 事件: {event_type}")
    
    # 只处理 push 事件
    if event_type != "push":
        logger.info(f"忽略非 push 事件: {event_type}")
        return MessageResponse(message=f"Event {event_type} ignored")
    
    # 获取推送信息
    ref = payload.get("ref", "")
    repo_name = payload.get("repository", {}).get("full_name", "unknown")
    pusher = payload.get("pusher", {}).get("name", "unknown")
    
    logger.info(f"收到推送: {repo_name} | 分支: {ref} | 推送者: {pusher}")
    
    # 只处理主分支（master 或 main）
    if ref not in ["refs/heads/master", "refs/heads/main"]:
        logger.info(f"忽略非主分支推送: {ref}")
        return MessageResponse(message=f"Branch {ref} ignored")
    
    # 添加后台任务执行部署
    background_tasks.add_task(run_deployment)
    
    logger.info("已将部署任务加入后台队列")
    return MessageResponse(message="Deployment started")


@router.get("/test", response_model=MessageResponse)
def test_webhook():
    """
    测试 webhook 端点是否可访问
    """
    return MessageResponse(message="Webhook endpoint is working")
