"""
SQLAlchemyモデル定義

このモジュールはデータベースのテーブル構造を定義します。
SQLAlchemy 2.0スタイルの宣言的マッピングを使用しています。
"""
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemyベースクラス
    
    全てのモデルクラスはこのクラスを継承します。
    共通のカラムや機能を追加する場合はここに定義します。
    """
    pass


class User(Base):
    """
    ユーザーモデル
    
    ユーザー情報を管理するテーブルです。
    
    Attributes:
        id: ユーザーID（主キー）
        name: ユーザー名
        email: メールアドレス（ユニーク制約）
        created_at: 作成日時（UTC）
    """
    __tablename__ = "users"
    
    # SQLAlchemy 2.0スタイルの型ヒント付きマッピング
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    def __repr__(self) -> str:
        """
        デバッグ用の文字列表現
        
        Returns:
            モデルの文字列表現
        """
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        モデルを辞書形式に変換
        
        APIレスポンスなどで使用する際の辞書形式への変換です。
        
        Returns:
            モデルの辞書表現
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }