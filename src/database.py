from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config import settings
from src.models import Base


class DatabaseManager:
    """非同期データベース接続マネージャー"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # MySQL用の非同期接続URLを構築
            database_url = settings.database.url
        
        # 非同期エンジンの作成（高トラフィック対応）
        self.engine = create_async_engine(
            database_url,
            echo=settings.debug,
            pool_size=settings.database.pool_max_size,
            max_overflow=settings.database.max_overflow,
            pool_pre_ping=True,  # 接続の有効性を確認
            pool_recycle=settings.database.pool_recycle,
            pool_timeout=settings.database.pool_timeout,
            connect_args={
                "server_settings": {
                    "application_name": "async-starter-api"
                },
                "command_timeout": 60,
            }
        )
        
        # セッションファクトリの作成
        self.async_session_maker = async_sessionmaker(
            self.engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self):
        """テーブルを作成"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """テーブルを削除"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """非同期セッションを取得"""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """データベース接続を閉じる"""
        await self.engine.dispose()


# グローバルインスタンス
db_manager = DatabaseManager()