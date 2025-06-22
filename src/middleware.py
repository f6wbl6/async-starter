"""
カスタムミドルウェア定義

このモジュールはFastAPIアプリケーション用の各種ミドルウェアを提供します。
リクエストログ、レート制限、データベース接続監視などの機能を含みます。
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from uuid import uuid4

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    リクエストのロギングミドルウェア
    
    全てのHTTPリクエストとレスポンスをログに記録し、
    処理時間やリクエストIDなどの追跡情報を提供します。
    
    機能:
    - ユニークなリクエストIDの生成
    - リクエスト処理時間の計測
    - 構造化ログの出力
    - レスポンスヘッダーへの情報追加
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        リクエストを処理し、ログを記録
        
        Args:
            request: HTTPリクエストオブジェクト
            call_next: 次のミドルウェアまたはエンドポイント
            
        Returns:
            HTTPレスポンス（追加ヘッダー付き）
        """
        # リクエストIDを生成
        request_id = str(uuid4())
        
        # リクエスト開始時刻
        start_time = time.time()
        
        # リクエストログ
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )
        
        # リクエストを処理
        response = await call_next(request)
        
        # 処理時間を計算
        process_time = time.time() - start_time
        
        # レスポンスヘッダーに情報を追加
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # レスポンスログ
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    シンプルなレート制限ミドルウェア
    
    メモリベースのレート制限機能を提供します。
    本番環境では Redis を使った分散レート制限を推奨します。
    
    警告:
        このミドルウェアはメモリ内にリクエスト履歴を保存するため、
        複数のワーカープロセスがある場合は適切に動作しません。
        本番環境では外部ストア（Redis等）を使用してください。
    
    Attributes:
        requests_per_minute: 1分間あたりの許可リクエスト数
        request_times: クライアントごとのリクエスト履歴
    """
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        """
        レート制限ミドルウェアを初期化
        
        Args:
            app: ASGIアプリケーション
            requests_per_minute: 1分間あたりの許可リクエスト数
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_times = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        レート制限チェックを実行
        
        クライアントIPベースでリクエスト数を制限します。
        制限を超えた場合は429 Too Many Requestsを返します。
        
        Args:
            request: HTTPリクエストオブジェクト
            call_next: 次のミドルウェアまたはエンドポイント
            
        Returns:
            HTTPレスポンス（制限時は429ステータス）
        """
        # クライアントIPを取得
        client_ip = request.client.host if request.client else "unknown"
        
        # 現在時刻
        current_time = time.time()
        
        # クライアントのリクエスト履歴を取得
        if client_ip not in self.request_times:
            self.request_times[client_ip] = []
        
        # 1分以内のリクエストのみを保持
        self.request_times[client_ip] = [
            t for t in self.request_times[client_ip]
            if current_time - t < 60
        ]
        
        # レート制限チェック
        if len(self.request_times[client_ip]) >= self.requests_per_minute:
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"}
            )
        
        # リクエスト時刻を記録
        self.request_times[client_ip].append(current_time)
        
        # リクエストを処理
        response = await call_next(request)
        
        return response


class DatabaseConnectionMiddleware(BaseHTTPMiddleware):
    """
    データベース接続の健全性をチェックするミドルウェア
    
    各リクエスト処理時にデータベース接続プールの状態を監視し、
    デバッグログにプール統計情報を出力します。
    
    機能:
    - 接続プールサイズの監視
    - アクティブ接続数の追跡
    - オーバーフロー接続の監視
    - ヘルスチェックエンドポイントのスキップ
    
    Note:
        ヘルスチェックエンドポイント（/health）では
        このミドルウェアの処理をスキップします。
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        データベース接続プールの状態を監視
        
        Args:
            request: HTTPリクエストオブジェクト
            call_next: 次のミドルウェアまたはエンドポイント
            
        Returns:
            HTTPレスポンス
        """
        # ヘルスチェックエンドポイントはスキップ
        if request.url.path == "/health":
            return await call_next(request)
        
        # データベース接続プールの状態をログ
        from src.database import db_manager
        pool = db_manager.engine.pool
        
        if pool:
            logger.debug(
                f"DB Pool status",
                extra={
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "overflow": pool.overflow(),
                    "total": pool.total()
                }
            )
        
        return await call_next(request)