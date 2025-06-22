"""
ユーザービジネスロジックサービス

このモジュールはユーザー関連のビジネスロジックを実装します。
リポジトリレイヤーとAPIレイヤーの間に位置し、
ビジネスルールの適用とドメイン固有の操作を担当します。
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories import UserRepository
from src.models import User
from src.schemas import UserCreate, UserUpdate


class UserService:
    """
    ユーザーサービス
    
    ユーザー関連のビジネスロジックを管理するサービスクラスです。
    リポジトリパターンを使用してデータアクセスを抽象化し、
    ビジネスルールの実装とエラーハンドリングを担当します。
    
    Attributes:
        db: データベースセッション
        repository: ユーザーリポジトリインスタンス
        
    責務:
    - ビジネスルールの適用
    - ドメイン例外の変換
    - トランザクション管理
    - データバリデーション
    """
    
    def __init__(self, db: AsyncSession) -> None:
        """
        ユーザーサービスを初期化
        
        Args:
            db: データベースセッション
        """
        self.db = db
        self.repository = UserRepository(db)
    
    async def get_users(self, page: int = 1, per_page: int = 20) -> tuple[list[User], int]:
        """
        ユーザー一覧を取得（ページネーション付き）
        
        指定されたページ番号と1ページあたりの表示数に基づいて
        ユーザー一覧を取得します。作成日時の降順で並び替えられます。
        
        Args:
            page: ページ番号（1から開始）
            per_page: 1ページあたりの表示数
            
        Returns:
            tuple: (ユーザーリスト, 総ユーザー数)
            
        Note:
            現在の実装では効率的なページネーション（LIMIT/OFFSET）ではなく、
            全データを取得してからメモリ上で切り出しています。
            大量データの場合はパフォーマンス改善が必要です。
        """
        # 総数を取得
        total = await self.repository.count()
        
        # ページネーション計算
        offset = (page - 1) * per_page
        
        # より効率的な実装: 直接ページネーション付きで取得
        users = await self.repository.get_paginated(offset, per_page)
        
        return list(users), total
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        ユーザーをIDで取得
        
        指定されたIDのユーザーを取得します。
        
        Args:
            user_id: 取得するユーザーのID
            
        Returns:
            ユーザーオブジェクト（存在しない場合はNone）
        """
        return await self.repository.get_by_id(user_id)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        新規ユーザーを作成
        
        ユーザー作成データを受け取り、新しいユーザーをデータベースに作成します。
        メールアドレスの重複チェックを行います。
        
        Args:
            user_data: 作成するユーザーのデータ
            
        Returns:
            作成されたユーザーオブジェクト
            
        Raises:
            ValueError: メールアドレスが既に存在する場合
            
        Note:
            作成日時は自動的に設定されます。
            メールアドレスはユニーク制約により重複を防いでいます。
        """
        try:
            return await self.repository.create(
                name=user_data.name,
                email=user_data.email
            )
        except IntegrityError:
            raise ValueError("Email already exists")
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        ユーザー情報を更新
        
        指定されたユーザーIDのユーザー情報を部分的に更新します。
        更新対象フィールドのバリデーションとメールアドレス重複チェックを行います。
        
        Args:
            user_id: 更新するユーザーのID
            user_data: 更新するユーザーデータ（部分更新可能）
            
        Returns:
            更新されたユーザーオブジェクト（存在しない場合はNone）
            
        Raises:
            ValueError: 
                - 更新するフィールドが指定されていない場合
                - メールアドレスが既に存在する場合
                
        Note:
            指定されたフィールドのみが更新され、
            未指定のフィールドは既存の値が保持されます。
        """
        # 更新するフィールドがない場合
        if not user_data.model_dump(exclude_unset=True):
            raise ValueError("No fields to update")
        
        try:
            return await self.repository.update(
                user_id,
                name=user_data.name,
                email=user_data.email
            )
        except IntegrityError:
            raise ValueError("Email already exists")
    
    async def delete_user(self, user_id: int) -> bool:
        """
        ユーザーを削除
        
        指定されたユーザーIDのユーザーをデータベースから削除します。
        物理削除（完全削除）を実行します。
        
        Args:
            user_id: 削除するユーザーのID
            
        Returns:
            削除に成功した場合True、対象ユーザーが存在しない場合False
            
        Warning:
            この操作は元に戻せません。
            本番環境では論理削除（削除フラグ）の使用を検討してください。
        """
        return await self.repository.delete(user_id)