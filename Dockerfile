# GKE向け最適化Dockerfile
# マルチステージビルドによるイメージサイズ最適化とセキュリティ強化

# ==============================================================================
# Build Stage: 依存関係のインストールとアプリケーションのビルド
# ==============================================================================
FROM python:3.11-slim as builder

# ビルド用の環境変数
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# システムパッケージの更新とビルド依存関係のインストール
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# uvパッケージマネージャーのインストール
RUN pip install uv

# 作業ディレクトリの設定
WORKDIR /app

# プロジェクト設定ファイルをコピー
COPY pyproject.toml ./

# 依存関係のインストール（プロダクション用）
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install -r pyproject.toml

# ==============================================================================
# Runtime Stage: 実行用の軽量イメージ
# ==============================================================================
FROM python:3.11-slim as runtime

# ランタイム用の環境変数
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    # GKE環境用の設定
    ENVIRONMENT=production \
    PORT=8080 \
    WORKERS=4 \
    LOG_LEVEL=info

# 実行時依存関係のインストール
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 非rootユーザーの作成（セキュリティ強化）
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /bin/bash appuser

# ビルドステージから仮想環境をコピー
COPY --from=builder /opt/venv /opt/venv

# 作業ディレクトリの設定
WORKDIR /app

# アプリケーションファイルをコピー
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser run.py ./
COPY --chown=appuser:appuser pyproject.toml ./

# ファイル権限の設定
RUN chmod -R 755 /app && \
    chown -R appuser:appuser /app

# 非rootユーザーに切り替え
USER appuser

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8080}/health', timeout=5)" || exit 1

# ポート公開（GKEのデフォルトポート8080を使用）
EXPOSE 8080

# アプリケーション起動
CMD ["python", "run.py"]

# ==============================================================================
# イメージメタデータ
# ==============================================================================
LABEL maintainer="async-starter-team" \
      version="1.0.0" \
      description="High-performance FastAPI application for GKE" \
      python.version="3.11" \
      framework="FastAPI" \
      platform="GKE"