from typing import Literal
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """データベース設定"""
    
    # 基本接続設定
    host: str = Field(default="localhost", description="データベースホスト")
    port: int = Field(default=3306, description="データベースポート", ge=1, le=65535)
    user: str = Field(default="testuser", description="データベースユーザー名")
    password: str = Field(default="testpass", description="データベースパスワード")
    name: str = Field(default="testdb", description="データベース名")
    
    # 接続プール設定（高トラフィック対応）
    pool_min_size: int = Field(default=5, description="最小接続数", ge=1)
    pool_max_size: int = Field(default=20, description="最大接続数", ge=1)
    pool_recycle: int = Field(default=3600, description="接続リサイクル時間（秒）", ge=60)
    pool_timeout: int = Field(default=30, description="接続タイムアウト（秒）", ge=1)
    max_overflow: int = Field(default=10, description="オーバーフロー許容数", ge=0)
    
    @computed_field
    @property
    def url(self) -> str:
        """データベース接続URLを構築"""
        return f"mysql+aiomysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    model_config = SettingsConfigDict(env_prefix="DB_")


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # アプリケーション基本設定
    debug: bool = Field(default=False, description="デバッグモード")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", 
        description="実行環境"
    )
    
    # セキュリティ設定
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="セッション暗号化キー",
        min_length=32
    )
    
    # API設定
    api_title: str = Field(default="Async Starter API", description="API名")
    api_version: str = Field(default="1.0.0", description="APIバージョン")
    api_description: str = Field(
        default="高トラフィック対応の非同期データベースAPI",
        description="API説明"
    )
    
    # CORS設定
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS許可オリジン"
    )
    
    # ログ設定
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="ログレベル"
    )
    
    # データベース設定
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    @computed_field
    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.environment == "development"
    
    @computed_field
    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.environment == "production"
    
    @computed_field
    @property
    def docs_url(self) -> str | None:
        """APIドキュメントURL（本番環境では無効）"""
        return "/docs" if not self.is_production else None
    
    @computed_field
    @property
    def redoc_url(self) -> str | None:
        """ReDocURL（本番環境では無効）"""
        return "/redoc" if not self.is_production else None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 未知の環境変数を無視
    )


# シングルトンインスタンス
settings = Settings()


# 後方互換性のためのエイリアス（段階的移行用）
config = settings