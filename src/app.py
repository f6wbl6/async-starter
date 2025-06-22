"""
FastAPIアプリケーションのエントリーポイント

このモジュールはFastAPIアプリケーションの設定、ミドルウェア、
エラーハンドラー、ルーターの登録を行います。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.database import db_manager
from src.middleware import (
    DatabaseConnectionMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
)
from src.routers import health, users
from src.schemas import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理
    
    アプリケーションの起動・終了時の処理を定義します。
    
    Args:
        app: FastAPIアプリケーションインスタンス
        
    Yields:
        None: アプリケーション実行中
    """
    # 起動時の処理
    print(f"Starting {settings.api_title} v{settings.api_version}...")
    
    if settings.is_development:
        # 開発環境ではテーブルを自動作成
        print("Creating database tables...")
        await db_manager.create_tables()
        print("Database tables created successfully")
    
    yield
    
    # 終了時の処理
    print("Shutting down...")
    await db_manager.close()
    print("Database connections closed")


def create_application() -> FastAPI:
    """
    FastAPIアプリケーションを作成
    
    アプリケーションインスタンスを作成し、各種設定を行います。
    
    Returns:
        設定済みのFastAPIアプリケーション
    """
    application = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan,
        docs_url=settings.docs_url,  # 本番環境では自動的にNone
        redoc_url=settings.redoc_url,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )
    
    # ミドルウェアの設定
    setup_middleware(application)
    
    # ルーターの登録
    setup_routers(application)
    
    # エラーハンドラーの設定
    setup_error_handlers(application)
    
    return application


def setup_middleware(app: FastAPI) -> None:
    """
    ミドルウェアを設定
    
    注意: ミドルウェアは後に追加したものが先に実行されます。
    
    Args:
        app: FastAPIアプリケーション
    """
    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    
    # リクエストロギング
    app.add_middleware(RequestLoggingMiddleware)
    
    # レート制限（本番環境のみ）
    if settings.is_production:
        app.add_middleware(
            RateLimitMiddleware, 
            requests_per_minute=100
        )
    
    # データベース接続監視
    app.add_middleware(DatabaseConnectionMiddleware)


def setup_routers(app: FastAPI) -> None:
    """
    APIルーターを登録
    
    Args:
        app: FastAPIアプリケーション
    """
    # ヘルスチェック
    app.include_router(
        health.router,
        tags=["Health"],
        include_in_schema=True
    )
    
    # ユーザー管理API
    app.include_router(
        users.router,
        tags=["Users"],
        include_in_schema=True
    )


def setup_error_handlers(app: FastAPI) -> None:
    """
    エラーハンドラーを設定
    
    Args:
        app: FastAPIアプリケーション
    """
    
    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, 
        exc: ValueError
    ) -> JSONResponse:
        """
        ValueErrorのハンドリング
        
        ビジネスロジックのバリデーションエラーなどを処理します。
        """
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                detail=str(exc),
                code="VALUE_ERROR"
            ).model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """
        一般的な例外のハンドリング
        
        予期しないエラーをキャッチし、適切なレスポンスを返します。
        """
        # 本番環境では詳細なエラー情報を隠す
        if settings.debug:
            detail = f"{type(exc).__name__}: {str(exc)}"
        else:
            detail = "Internal server error"
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=detail,
                code="INTERNAL_ERROR"
            ).model_dump()
        )


# アプリケーションインスタンスの作成
app = create_application()