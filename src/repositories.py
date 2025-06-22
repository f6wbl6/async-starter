"""
データアクセスレイヤー（リポジトリパターン）

このモジュールはデータベースアクセスのロジックを提供します。
ビジネスロジックとデータアクセスロジックを分離し、テストしやすい構造にしています。
"""
from typing import Optional, Sequence

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User


class UserRepository:
    """
    ユーザーリポジトリ
    
    ユーザーテーブルに対するCRUD操作を提供します。
    SQLAlchemy 2.0スタイルのクエリを使用しています。
    
    Attributes:
        session: 非同期データベースセッション
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        リポジトリを初期化
        
        Args:
            session: 非同期データベースセッション
        """
        self.session = session
    
    async def get_all(self) -> Sequence[User]:
        """
        全ユーザーを取得
        
        Returns:
            ユーザーのリスト
        """
        stmt = select(User).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        IDでユーザーを取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            ユーザーオブジェクト（存在しない場合はNone）
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        メールアドレスでユーザーを取得
        
        Args:
            email: メールアドレス
            
        Returns:
            ユーザーオブジェクト（存在しない場合はNone）
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_paginated(self, offset: int = 0, limit: int = 20) -> Sequence[User]:
        """
        ページネーション付きでユーザーを取得
        
        Args:
            offset: オフセット
            limit: 取得件数
            
        Returns:
            ユーザーのリスト
        """
        stmt = (
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create(self, name: str, email: str) -> User:
        """
        新規ユーザーを作成
        
        Args:
            name: ユーザー名
            email: メールアドレス
            
        Returns:
            作成されたユーザーオブジェクト
        """
        user = User(name=name, email=email)
        self.session.add(user)
        await self.session.flush()  # IDを取得するためにflush
        await self.session.refresh(user)  # 作成されたデータを再読み込み
        return user
    
    async def update(
        self, 
        user_id: int, 
        name: Optional[str] = None, 
        email: Optional[str] = None
    ) -> Optional[User]:
        """
        ユーザー情報を更新
        
        Args:
            user_id: ユーザーID
            name: 新しいユーザー名（省略可）
            email: 新しいメールアドレス（省略可）
            
        Returns:
            更新されたユーザーオブジェクト（存在しない場合はNone）
        """
        # 更新する値を準備
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if email is not None:
            update_data['email'] = email
        
        if not update_data:
            # 更新する値がない場合は既存のユーザーを返す
            return await self.get_by_id(user_id)
        
        # SQLAlchemy 2.0スタイルの更新
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()
    
    async def delete(self, user_id: int) -> bool:
        """
        ユーザーを削除
        
        Args:
            user_id: ユーザーID
            
        Returns:
            削除に成功した場合True
        """
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
    
    async def count(self) -> int:
        """
        ユーザー数を取得
        
        Returns:
            ユーザーの総数
        """
        stmt = select(func.count()).select_from(User)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def exists(self, user_id: int) -> bool:
        """
        ユーザーの存在確認
        
        Args:
            user_id: ユーザーID
            
        Returns:
            存在する場合True
        """
        stmt = select(exists().where(User.id == user_id))
        result = await self.session.execute(stmt)
        return bool(result.scalar())