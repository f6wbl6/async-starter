# GKE デプロイメントガイド

このガイドでは、FastAPIアプリケーションをGoogle Kubernetes Engine (GKE) にデプロイする方法を説明します。

## 目次

1. [前提条件](#前提条件)
2. [コンテナ化の概要](#コンテナ化の概要)
3. [ローカル開発環境](#ローカル開発環境)
4. [GKEへのデプロイ](#gkeへのデプロイ)
5. [運用とモニタリング](#運用とモニタリング)
6. [トラブルシューティング](#トラブルシューティング)

## 前提条件

### 必要なツール

```bash
# Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Docker
# macOS: Docker Desktop をインストール
# Linux: パッケージマネージャーでインストール

# kubectl
gcloud components install kubectl
```

### Google Cloud の設定

```bash
# 認証
gcloud auth login

# プロジェクトの作成（必要に応じて）
gcloud projects create YOUR_PROJECT_ID

# プロジェクトの設定
gcloud config set project YOUR_PROJECT_ID

# 必要なAPIの有効化
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## コンテナ化の概要

### Dockerfileの特徴

このプロジェクトのDockerfileは以下の最適化を行っています：

#### 1. マルチステージビルド
```dockerfile
# ビルドステージ
FROM python:3.11-slim as builder
# 依存関係のインストール

# 実行ステージ
FROM python:3.11-slim as runtime
# 軽量なランタイムイメージ
```

**メリット**:
- イメージサイズの最小化
- ビルド時間の短縮
- セキュリティの向上

#### 2. セキュリティ強化
```dockerfile
# 非rootユーザーでの実行
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# セキュリティコンテキスト
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
```

#### 3. パフォーマンス最適化
```dockerfile
# uvパッケージマネージャーの使用
RUN pip install uv
RUN uv pip install -r pyproject.toml

# 環境変数の最適化
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
```

### 環境変数設定

| 変数名 | デフォルト | 説明 |
|--------|------------|------|
| `ENVIRONMENT` | `production` | 実行環境 |
| `PORT` | `8080` | アプリケーションポート |
| `WORKERS` | `4` | ワーカープロセス数 |
| `LOG_LEVEL` | `info` | ログレベル |
| `DB_HOST` | `localhost` | データベースホスト |
| `DB_PORT` | `3306` | データベースポート |
| `DB_USER` | - | データベースユーザー |
| `DB_PASSWORD` | - | データベースパスワード |
| `DB_NAME` | - | データベース名 |

## ローカル開発環境

### Docker Composeを使用した開発

```bash
# 開発環境の起動
docker-compose up -d

# ログの確認
docker-compose logs -f app

# 停止
docker-compose down
```

### サービス構成

- **app**: FastAPIアプリケーション (ポート: 8000)
- **mysql**: MySQL 8.0 データベース (ポート: 3306)
- **redis**: Redis キャッシュ (ポート: 6379)

### 開発時の機能

- **ホットリロード**: ソースコード変更時の自動再起動
- **デバッグログ**: 詳細なログ出力
- **ヘルスチェック**: 各サービスの健全性監視

## GKEへのデプロイ

### 自動デプロイスクリプト

```bash
# 基本的な使用方法
./deploy-gke.sh -p YOUR_PROJECT_ID

# カスタム設定
./deploy-gke.sh -p YOUR_PROJECT_ID -c my-cluster -z asia-northeast1-b
```

### 手動デプロイ手順

#### 1. Dockerイメージのビルドとプッシュ

```bash
# イメージのビルド
docker build -t gcr.io/YOUR_PROJECT_ID/async-starter:latest .

# GCRへのプッシュ
docker push gcr.io/YOUR_PROJECT_ID/async-starter:latest
```

#### 2. GKEクラスターの作成

```bash
gcloud container clusters create async-starter-cluster \
  --zone=asia-northeast1-a \
  --num-nodes=3 \
  --machine-type=e2-standard-2 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10
```

#### 3. Kubernetesマニフェストの適用

```bash
# Secretの作成（機密情報）
kubectl create secret generic async-starter-secret \
  --from-literal=DB_USER=your_db_user \
  --from-literal=DB_PASSWORD=your_db_password

# マニフェストの適用
kubectl apply -f kubernetes.yaml

# デプロイ状況の確認
kubectl rollout status deployment/async-starter-deployment
```

### Kubernetesリソース

#### Deployment
- **レプリカ数**: 3（高可用性）
- **リソース制限**: CPU 1000m, Memory 512Mi
- **ヘルスチェック**: Liveness/Readiness プローブ

#### Service
- **タイプ**: ClusterIP
- **ポート**: 80 → 8080

#### HorizontalPodAutoscaler
- **最小レプリカ**: 3
- **最大レプリカ**: 20
- **メトリクス**: CPU 70%, Memory 80%

#### PodDisruptionBudget
- **最小利用可能**: 2ポッド

## 運用とモニタリング

### ヘルスチェック

```bash
# アプリケーションのヘルスチェック
curl http://YOUR_EXTERNAL_IP/health

# Kubernetesリソースの確認
kubectl get pods,svc,hpa -l app=async-starter
```

### ログ確認

```bash
# アプリケーションログ
kubectl logs -l app=async-starter -f

# 特定のポッドのログ
kubectl logs POD_NAME -f

# 前回のコンテナのログ（クラッシュ時）
kubectl logs POD_NAME --previous
```

### スケーリング

```bash
# 手動スケーリング
kubectl scale deployment async-starter-deployment --replicas=5

# オートスケーラーの状態確認
kubectl get hpa async-starter-hpa
```

### アップデート

```bash
# 新しいイメージでの更新
kubectl set image deployment/async-starter-deployment \
  async-starter=gcr.io/YOUR_PROJECT_ID/async-starter:NEW_TAG

# ローリングアップデートの状況確認
kubectl rollout status deployment/async-starter-deployment

# ロールバック
kubectl rollout undo deployment/async-starter-deployment
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. ポッドが起動しない

```bash
# ポッドの詳細確認
kubectl describe pod POD_NAME

# イベントの確認
kubectl get events --sort-by=.metadata.creationTimestamp
```

**よくある原因**:
- イメージのプル失敗
- リソース不足
- 設定ミス

#### 2. データベース接続エラー

```bash
# Secret の確認
kubectl get secret async-starter-secret -o yaml

# ConfigMap の確認
kubectl get configmap async-starter-config -o yaml
```

**チェックポイント**:
- データベースホスト名
- 認証情報
- ネットワーク設定

#### 3. パフォーマンス問題

```bash
# リソース使用量の確認
kubectl top pods -l app=async-starter

# HPA状態の確認
kubectl describe hpa async-starter-hpa
```

**対応方法**:
- リソース制限の調整
- ワーカー数の最適化
- データベース接続プールの調整

### デバッグ用コマンド

```bash
# ポッドへの接続
kubectl exec -it POD_NAME -- /bin/bash

# ポートフォワード
kubectl port-forward service/async-starter-service 8080:80

# ログストリーミング
kubectl logs -l app=async-starter -f --tail=100
```

## セキュリティベストプラクティス

### 1. Secret管理

```bash
# Google Secret Manager の使用
gcloud secrets create db-password --data-file=password.txt

# Kubernetes Secret の暗号化
kubectl create secret generic db-secret --from-literal=password=SECRET
```

### 2. ネットワークセキュリティ

```yaml
# NetworkPolicy の例
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: async-starter-netpol
spec:
  podSelector:
    matchLabels:
      app: async-starter
  policyTypes:
  - Ingress
  - Egress
```

### 3. RBAC設定

```yaml
# ServiceAccount の作成
apiVersion: v1
kind: ServiceAccount
metadata:
  name: async-starter-sa
```

## 監視とアラート

### Google Cloud Monitoring

```bash
# モニタリングの有効化
gcloud services enable monitoring.googleapis.com

# アラートポリシーの作成
# Cloud Consoleから設定
```

### Prometheus + Grafana（オプション）

```bash
# Helm での Prometheus インストール
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

## コスト最適化

### リソース最適化

1. **適切なマシンタイプの選択**
   - CPU: e2-standard-2（開発）→ c2-standard-4（本番）
   - メモリ: 要求に応じて調整

2. **オートスケーリングの活用**
   - 最小ノード数: 1
   - 最大ノード数: 用途に応じて設定

3. **Spot VM の活用**
   ```bash
   gcloud container node-pools create spot-pool \
     --cluster=async-starter-cluster \
     --spot \
     --num-nodes=2
   ```

## まとめ

このGKEデプロイメント設定により、以下が実現されます：

- **高可用性**: 複数レプリカとヘルスチェック
- **スケーラビリティ**: オートスケーリング対応
- **セキュリティ**: 非rootユーザー実行と適切な権限設定
- **運用性**: 包括的なログとモニタリング
- **パフォーマンス**: 最適化されたコンテナとK8s設定

本番環境での運用前に、必ずテスト環境での動作確認を行ってください。