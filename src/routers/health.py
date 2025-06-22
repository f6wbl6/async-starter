"""
ヘルスチェックAPIルーター

このモジュールはアプリケーションの健全性をチェックするAPIエンドポイントを提供します。
システム監視やロードバランサーのヘルスチェックに使用されます。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.config import settings
from src.dependencies import get_db
from src.schemas import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    ヘルスチェックエンドポイント
    
    アプリケーションとデータベースの健全性をチェックし、
    システムの状態を報告します。
    
    チェック項目:
    - データベース接続の確認
    - アプリケーションバージョンの報告
    - 現在時刻の報告
    
    Args:
        db: データベースセッション（依存性注入）
        
    Returns:
        HealthCheckResponse: システムの健全性情報
        
    Raises:
        HTTPException: データベースエラーが発生した場合でも、
                      statusは"healthy"のまま、database項目で状態を報告
                      
    Note:
        このエンドポイントは認証不要で、システム監視ツールや
        ロードバランサーから頻繁にアクセスされることを想定しています。
    """
    try:
        # データベース接続確認（SQLAlchemy 2.0スタイル）
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return HealthCheckResponse(
        status="healthy",
        database=db_status,
        version=settings.api_version
    )