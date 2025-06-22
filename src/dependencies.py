"""
FastAPI依存性注入定義

このモジュールはFastAPIアプリケーションで使用される依存性注入関数を定義します。
主にデータベースセッションの管理を担当し、リクエストごとのライフサイクル管理を行います。
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    データベースセッションの依存性注入
    
    FastAPIのDependsで使用され、各リクエストごとに新しいデータベースセッションを
    作成し、リクエスト終了時に自動的にクローズします。
    
    Usage:
        ```python
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # セッションを使用してデータベースアクセス
            pass
        ```
    
    Yields:
        AsyncSession: SQLAlchemyの非同期セッション
        
    Note:
        セッションは自動的にトランザクション管理され、例外が発生した場合は
        ロールバックされます。正常終了時はコミットされます。
    """
    async with db_manager.get_session() as session:
        yield session