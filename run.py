"""
アプリケーションエントリーポイント

GKE環境での運用を想定し、環境変数による設定制御と
Graceful shutdownに対応したエントリーポイントです。
"""
import os
import signal
import sys
import multiprocessing

import uvicorn
from src.config import settings


def get_worker_count() -> int:
    """
    ワーカー数を環境変数またはCPUコア数から決定
    
    Returns:
        ワーカー数
    """
    workers = os.getenv("WORKERS")
    if workers:
        return int(workers)
    
    # CPUコア数 x 2 + 1 (Gunicornの推奨設定)
    return (multiprocessing.cpu_count() * 2) + 1


def get_port() -> int:
    """
    ポート番号を環境変数から取得
    
    Returns:
        ポート番号（デフォルト: 8000）
    """
    return int(os.getenv("PORT", "8000"))


def get_log_level() -> str:
    """
    ログレベルを環境変数から取得
    
    Returns:
        ログレベル（デフォルト: info）
    """
    return os.getenv("LOG_LEVEL", "info").lower()


def signal_handler(signum: int, frame=None) -> None:
    """
    Graceful shutdown用のシグナルハンドラー
    
    Args:
        signum: シグナル番号
        frame: フレームオブジェクト（未使用）
    """
    print(f"Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)


def main() -> None:
    """
    アプリケーションのメインエントリーポイント
    
    環境変数に基づいて開発環境または本番環境の設定で起動します。
    GKE環境では本番環境設定が使用されます。
    """
    # Graceful shutdown用のシグナルハンドラー設定
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    port = get_port()
    log_level = get_log_level()
    
    print(f"Starting application on port {port} with log level {log_level}")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    
    if settings.is_development:
        # 開発環境：ホットリロード有効
        print("Running in development mode with hot reload")
        uvicorn.run(
            "src.app:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level=log_level,
            access_log=True
        )
    else:
        # 本番環境：Gunicornと同等の設定でUvicornを使用
        # GKE環境では通常こちらが使用される
        worker_count = get_worker_count()
        print(f"Running in production mode with {worker_count} workers")
        
        uvicorn.run(
            "src.app:app",
            host="0.0.0.0",
            port=port,
            workers=worker_count,
            loop="uvloop",  # 高性能イベントループ
            log_level=log_level,
            access_log=True,
            # プロダクション設定
            limit_concurrency=1000,
            limit_max_requests=1000,
            timeout_keep_alive=5,
            # Graceful shutdown設定
            timeout_graceful_shutdown=30
        )


if __name__ == "__main__":
    main()