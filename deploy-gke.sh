#!/bin/bash

# GKE デプロイメントスクリプト
# FastAPI アプリケーションを Google Kubernetes Engine にデプロイ

set -euo pipefail

# 設定変数
PROJECT_ID=${PROJECT_ID:-""}
CLUSTER_NAME=${CLUSTER_NAME:-"async-starter-cluster"}
ZONE=${ZONE:-"asia-northeast1-a"}
IMAGE_NAME="async-starter"
SERVICE_NAME="async-starter-service"

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 使用方法を表示
usage() {
    cat << EOF
使用方法: $0 [OPTIONS]

GKE への FastAPI アプリケーションデプロイスクリプト

オプション:
    -p, --project-id PROJECT_ID    Google Cloud プロジェクト ID (必須)
    -c, --cluster CLUSTER_NAME     GKE クラスター名 (デフォルト: async-starter-cluster)
    -z, --zone ZONE               GKE ゾーン (デフォルト: asia-northeast1-a)
    -h, --help                    このヘルプを表示

環境変数:
    PROJECT_ID                    Google Cloud プロジェクト ID
    CLUSTER_NAME                  GKE クラスター名
    ZONE                         GKE ゾーン

例:
    $0 -p my-project-id
    PROJECT_ID=my-project-id $0
EOF
}

# パラメータ解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        -c|--cluster)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        -z|--zone)
            ZONE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            usage
            exit 1
            ;;
    esac
done

# プロジェクトIDの確認
if [[ -z "$PROJECT_ID" ]]; then
    log_error "PROJECT_ID が設定されていません"
    usage
    exit 1
fi

# 必要なツールの確認
check_dependencies() {
    log_info "依存関係の確認中..."
    
    local tools=("docker" "gcloud" "kubectl")
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "以下のツールがインストールされていません: ${missing_tools[*]}"
        exit 1
    fi
    
    log_success "すべての依存関係が確認されました"
}

# Google Cloud の認証確認
check_gcloud_auth() {
    log_info "Google Cloud の認証確認中..."
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Google Cloud に認証されていません"
        log_info "以下のコマンドで認証してください: gcloud auth login"
        exit 1
    fi
    
    # プロジェクトの設定
    gcloud config set project "$PROJECT_ID"
    log_success "プロジェクト $PROJECT_ID に設定されました"
}

# Dockerイメージのビルド
build_image() {
    log_info "Dockerイメージをビルド中..."
    
    local image_tag="gcr.io/$PROJECT_ID/$IMAGE_NAME:$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"
    
    docker build -t "$image_tag" .
    docker tag "$image_tag" "gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"
    
    log_success "イメージビルド完了: $image_tag"
    echo "$image_tag"
}

# イメージをGCRにプッシュ
push_image() {
    local image_tag="$1"
    
    log_info "イメージを Google Container Registry にプッシュ中..."
    
    # GCR認証の設定
    gcloud auth configure-docker --quiet
    
    docker push "$image_tag"
    docker push "gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"
    
    log_success "イメージプッシュ完了"
}

# GKEクラスターへの接続
connect_cluster() {
    log_info "GKE クラスターに接続中..."
    
    if ! gcloud container clusters describe "$CLUSTER_NAME" --zone="$ZONE" --project="$PROJECT_ID" &>/dev/null; then
        log_warning "クラスター $CLUSTER_NAME が見つかりません"
        log_info "クラスターを作成しますか? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            create_cluster
        else
            log_error "クラスターが必要です"
            exit 1
        fi
    fi
    
    gcloud container clusters get-credentials "$CLUSTER_NAME" --zone="$ZONE" --project="$PROJECT_ID"
    log_success "クラスターに接続されました"
}

# GKEクラスターの作成
create_cluster() {
    log_info "GKE クラスターを作成中..."
    
    gcloud container clusters create "$CLUSTER_NAME" \
        --zone="$ZONE" \
        --num-nodes=3 \
        --node-locations="$ZONE" \
        --machine-type="e2-standard-2" \
        --disk-size="50GB" \
        --enable-autorepair \
        --enable-autoupgrade \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=10 \
        --enable-ip-alias \
        --enable-network-policy \
        --project="$PROJECT_ID"
    
    log_success "クラスター作成完了"
}

# Kubernetesマニフェストの更新とデプロイ
deploy_application() {
    local image_tag="$1"
    
    log_info "Kubernetes マニフェストを更新中..."
    
    # kubernetes.yaml内のイメージタグを更新
    sed -i.bak "s|gcr.io/YOUR_PROJECT_ID/async-starter:latest|$image_tag|g" kubernetes.yaml
    
    log_info "アプリケーションをデプロイ中..."
    
    kubectl apply -f kubernetes.yaml
    
    # デプロイメントの完了を待機
    kubectl rollout status deployment/async-starter-deployment --timeout=300s
    
    # バックアップファイルを削除
    rm -f kubernetes.yaml.bak
    
    log_success "アプリケーションデプロイ完了"
}

# サービスの状態確認
check_service_status() {
    log_info "サービスの状態を確認中..."
    
    # Pod状態の確認
    kubectl get pods -l app=async-starter
    
    # サービス状態の確認
    kubectl get service "$SERVICE_NAME"
    
    # 外部IPの取得（Ingressが設定されている場合）
    local external_ip=""
    local timeout=60
    local count=0
    
    while [[ -z "$external_ip" && $count -lt $timeout ]]; do
        external_ip=$(kubectl get service "$SERVICE_NAME" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        if [[ -z "$external_ip" ]]; then
            sleep 5
            ((count+=5))
        fi
    done
    
    if [[ -n "$external_ip" ]]; then
        log_success "外部IP: $external_ip"
        log_info "ヘルスチェック: curl http://$external_ip/health"
    else
        log_warning "外部IPの取得がタイムアウトしました"
        log_info "ポートフォワードでアクセス可能: kubectl port-forward service/$SERVICE_NAME 8080:80"
    fi
}

# メイン処理
main() {
    log_info "GKE デプロイメント開始"
    log_info "プロジェクト: $PROJECT_ID"
    log_info "クラスター: $CLUSTER_NAME"
    log_info "ゾーン: $ZONE"
    
    check_dependencies
    check_gcloud_auth
    
    local image_tag
    image_tag=$(build_image)
    
    push_image "$image_tag"
    connect_cluster
    deploy_application "$image_tag"
    check_service_status
    
    log_success "デプロイメント完了!"
}

# エラートラップ
trap 'log_error "デプロイメント中にエラーが発生しました"; exit 1' ERR

# メイン処理の実行
main "$@"