#!/bin/bash

# FastAPI アプリケーション起動スクリプト

# 環境変数の読み込み
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# 環境に応じて起動方法を変更
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting in production mode with Gunicorn..."
    exec gunicorn src.app:app -c gunicorn_conf.py
else
    echo "Starting in development mode with Uvicorn..."
    exec python run.py
fi