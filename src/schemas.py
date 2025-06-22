"""
Pydanticスキーマ定義

このモジュールはAPIのリクエスト/レスポンスのスキーマを定義します。
Pydantic v2の最新機能を活用し、型安全性とバリデーションを提供します。
"""
from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """
    ユーザー基本スキーマ
    
    ユーザー情報の基本的なフィールドを定義します。
    他のユーザー関連スキーマのベースクラスとして使用されます。
    """
    name: Annotated[str, Field(
        min_length=1, 
        max_length=100,
        description="ユーザー名",
        examples=["田中太郎"]
    )]
    email: Annotated[EmailStr, Field(
        description="メールアドレス",
        examples=["tanaka@example.com"]
    )]
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """名前の前後の空白を削除"""
        return v.strip()


class UserCreate(UserBase):
    """
    ユーザー作成リクエストスキーマ
    
    新規ユーザー作成時のリクエストボディです。
    UserBaseを継承し、追加のフィールドは定義していません。
    """
    pass


class UserUpdate(BaseModel):
    """
    ユーザー更新リクエストスキーマ
    
    ユーザー情報更新時のリクエストボディです。
    全てのフィールドはOptionalで、指定されたフィールドのみ更新されます。
    """
    name: Optional[Annotated[str, Field(
        min_length=1,
        max_length=100,
        description="ユーザー名",
        examples=["田中太郎（更新）"]
    )]] = None
    email: Optional[Annotated[EmailStr, Field(
        description="メールアドレス",
        examples=["tanaka-updated@example.com"]
    )]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """名前の前後の空白を削除"""
        return v.strip() if v else v


class UserResponse(UserBase):
    """
    ユーザーレスポンススキーマ
    
    ユーザー情報のレスポンススキーマです。
    データベースモデルから自動的に変換されます。
    """
    id: Annotated[int, Field(
        description="ユーザーID",
        examples=[1]
    )]
    created_at: Annotated[datetime, Field(
        description="作成日時（UTC）",
        examples=["2024-01-01T00:00:00Z"]
    )]
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class UserListResponse(BaseModel):
    """
    ユーザー一覧レスポンススキーマ
    
    ユーザー一覧取得APIのレスポンススキーマです。
    ページネーション情報を含みます。
    """
    users: list[UserResponse] = Field(
        description="ユーザーリスト"
    )
    total: Annotated[int, Field(
        ge=0,
        description="総ユーザー数",
        examples=[100]
    )]
    page: Annotated[int, Field(
        ge=1,
        description="現在のページ番号",
        examples=[1]
    )]
    per_page: Annotated[int, Field(
        ge=1,
        le=100,
        description="1ページあたりの表示数",
        examples=[20]
    )]
    
    @property
    def total_pages(self) -> int:
        """総ページ数を計算"""
        return (self.total + self.per_page - 1) // self.per_page if self.total > 0 else 0
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": [
                    {
                        "id": 1,
                        "name": "田中太郎",
                        "email": "tanaka@example.com",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 100,
                "page": 1,
                "per_page": 20
            }
        }
    )


class ErrorResponse(BaseModel):
    """
    エラーレスポンススキーマ
    
    APIエラー時のレスポンススキーマです。
    """
    detail: Annotated[str, Field(
        description="エラーの詳細メッセージ",
        examples=["User not found"]
    )]
    code: Optional[Annotated[str, Field(
        description="エラーコード",
        examples=["USER_NOT_FOUND"]
    )]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "User with id 123 not found",
                "code": "USER_NOT_FOUND"
            }
        }
    )


class HealthCheckResponse(BaseModel):
    """
    ヘルスチェックレスポンススキーマ
    
    システムの健全性チェック用のレスポンススキーマです。
    """
    status: Annotated[str, Field(
        description="ヘルスステータス",
        examples=["healthy", "unhealthy"]
    )] = "healthy"
    timestamp: Annotated[datetime, Field(
        description="チェック時刻（UTC）",
        default_factory=lambda: datetime.now(timezone.utc)
    )]
    database: Annotated[str, Field(
        description="データベース接続状態",
        examples=["connected", "disconnected"]
    )]
    version: Annotated[str, Field(
        description="アプリケーションバージョン",
        examples=["1.0.0"]
    )]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "database": "connected",
                "version": "1.0.0"
            }
        }
    )