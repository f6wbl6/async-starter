import multiprocessing
import os

# Gunicorn設定ファイル（高トラフィック対応）

# バインドアドレス
bind = "0.0.0.0:8000"

# ワーカー数（CPUコア数 * 2 + 1 が推奨）
workers = multiprocessing.cpu_count() * 2 + 1

# ワーカークラス（uvicornのASGIワーカーを使用）
worker_class = "uvicorn.workers.UvicornWorker"

# ワーカーあたりの最大リクエスト数（メモリリーク対策）
max_requests = 1000
max_requests_jitter = 50

# タイムアウト設定
timeout = 60
graceful_timeout = 30
keepalive = 5

# プロセス名
proc_name = "async-starter-api"

# ログ設定
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"  # 標準出力
errorlog = "-"   # 標準エラー出力
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# プリロード（メモリ効率化）
preload_app = True

# ワーカー接続数
worker_connections = 1000

# その他の最適化
worker_tmp_dir = "/dev/shm"  # RAMディスクを使用（Linuxのみ）