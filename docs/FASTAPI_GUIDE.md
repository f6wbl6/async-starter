# 高トラフィック対応 FastAPI + 非同期データベースアプリケーション

このプロジェクトは、**FastAPI + SQLAlchemy 2.0 + Pydantic v2** を使用した高トラフィック対応の非同期Web APIの実装例です。プロダクション環境での運用を想定した最新のモダンな設計、パフォーマンス最適化、および業界標準のベストプラクティスが統合されています。

## 技術スタック

### コア技術
- **Python 3.11** - 最新の言語機能とパフォーマンス改善
- **FastAPI** - 高速な非同期Webフレームワーク
- **SQLAlchemy 2.0** - 非同期対応ORM
- **MySQL 8.0** - プロダクショングレードのデータベース

### パフォーマンス関連
- **Uvicorn** - ASGIサーバー（uvloop使用）
- **Gunicorn** - プロセスマネージャー
- **aiomysql** - 非同期MySQLドライバー

### 開発ツール
- **uv** - 高速Pythonパッケージマネージャー
- **pytest + pytest-asyncio** - 非同期テスト
- **python-dotenv** - 環境変数管理
- **Pydantic** - データバリデーション

## セットアップ

### 1. MySQLサーバーの起動

```bash
docker compose up -d
```

MySQLコンテナが起動し、初期データが自動的に投入されます。

### 2. 環境変数の設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集して適切な値を設定
# 特にデータベースのパスワードなど
```

### 3. Python環境のセットアップ

```bash
# uvをインストール（未インストールの場合）
pip install uv

# 依存関係のインストール
uv sync
```

### 4. アプリケーションの起動

```bash
# 開発環境（ホットリロード有効）
./start.sh

# または直接
python run.py

# 本番環境（Gunicorn使用）
ENVIRONMENT=production ./start.sh
```

### 5. APIドキュメントの確認

開発環境では、以下のURLで対話的なAPIドキュメントが利用可能：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6. テストの実行

```bash
# 全テストを実行
pytest

# APIテストのみ
pytest tests/test_api.py

# SQLAlchemyテストのみ
pytest tests/test_sqlalchemy.py
```

## FastAPIと非同期処理の解説

### 1. FastAPIの非同期処理アーキテクチャ

FastAPIはネイティブに非同期処理をサポートし、高トラフィックに対応できる設計です：

```python
@app.get("/api/v1/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    # データベースアクセス中も他のリクエストを処理可能
    users = await repo.get_all()
    return users
```

**メリット**：
- 少ないリソースで多くの同時接続を処理
- I/O待機時間の有効活用
- スケーラビリティの向上

### 2. 主要コンポーネント

#### DatabaseManager クラス

```python
class DatabaseManager:
    def __init__(self, database_url: str = None):
        self.engine = create_async_engine(
            database_url,
            echo=config.debug,
            pool_size=config.db_pool_max_size
        )
        self.async_session_maker = async_sessionmaker(
            self.engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )
```

#### 依存性注入による効率化

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # リクエストごとに新しいセッションを作成
    # 自動的にコミット/ロールバックを管理
    async with db_manager.get_session() as session:
        yield session
```

## 高トラフィック対応のポイント

### 1. データベース接続プールの最適化
```python
# 高トラフィック向け設定
DB_POOL_MIN_SIZE=5      # 最小接続数
DB_POOL_MAX_SIZE=20     # 最大接続数
DB_POOL_RECYCLE=3600    # 接続リサイクル時間
DB_MAX_OVERFLOW=10      # オーバーフロー許容数
```

### 2. プロセスマネージャーの活用
- **Gunicorn**: 複数ワーカープロセスで負荷分散
- **Uvicorn**: uvloopを使用した高速ASGIサーバー

### 3. ミドルウェアによる最適化
- **リクエストロギング**: パフォーマンス監視
- **レート制限**: DoS攻撃対策
- **データベース接続監視**: プール状態の追跡

## APIエンドポイント

### ヘルスチェック
- `GET /health` - サービスの健全性確認

### ユーザー管理
- `GET /api/v1/users` - ユーザー一覧（ページネーション対応）
- `GET /api/v1/users/{user_id}` - 特定ユーザーの取得
- `POST /api/v1/users` - 新規ユーザー作成
- `PATCH /api/v1/users/{user_id}` - ユーザー情報更新
- `DELETE /api/v1/users/{user_id}` - ユーザー削除

## リファクタリング完了サマリー

このプロジェクトは以下の最新技術とベストプラクティスを採用してリファクタリングされました：

### 主要な改善点

1. **SQLAlchemy 2.0 対応**
   - `Mapped[型]` による型安全なモデル定義
   - `mapped_column()` による統一されたカラム定義
   - `.returning()` 句による効率的な更新結果取得

2. **Pydantic v2 対応**
   - `Annotated` 型による高度なバリデーション
   - `BaseSettings` による環境変数管理
   - `computed_field` による動的プロパティ

3. **FastAPI アーキテクチャ改善**
   - ルーター分離による機能別API管理
   - サービスレイヤーによるビジネスロジック分離
   - 依存性注入による疎結合設計

4. **包括的docstring追加**
   - 全モジュール、クラス、関数に詳細な説明
   - 引数、戻り値、例外の完全な文書化
   - 使用例とベストプラクティスの提示

5. **カスタムミドルウェア実装**
   - リクエストロギングによる詳細な追跡
   - レート制限による DoS 攻撃対策
   - データベース接続プール監視

### 技術的負債の解消

- 非推奨構文の完全除去
- 型ヒントの改善と一貫性確保
- エラーハンドリングの標準化
- 設定管理の安全性向上

### 今後の拡張性

この基盤により、以下の機能追加が容易になりました：
- 認証・認可システム
- キャッシュレイヤー
- メトリクス収集
- 分散トレーシング
- API バージョニング

## 参考リンク

### FastAPI
- [FastAPI 公式ドキュメント](https://fastapi.tiangolo.com/)
- [FastAPI パフォーマンスガイド](https://fastapi.tiangolo.com/advanced/)
- [FastAPI デプロイメント](https://fastapi.tiangolo.com/deployment/)

### SQLAlchemy 2.0
- [SQLAlchemy 2.0 非同期ドキュメント](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [SQLAlchemy 2.0 マイグレーションガイド](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [SQLAlchemy パフォーマンスチューニング](https://docs.sqlalchemy.org/en/20/faq/performance.html)

### Pydantic v2
- [Pydantic v2 公式ドキュメント](https://docs.pydantic.dev/2.0/)
- [Pydantic パフォーマンス](https://docs.pydantic.dev/2.0/concepts/performance/)
- [Pydantic Settings](https://docs.pydantic.dev/2.0/usage/pydantic_settings/)

### サーバー & デプロイメント
- [Uvicorn 公式ドキュメント](https://www.uvicorn.org/)
- [Gunicorn 公式ドキュメント](https://gunicorn.org/)
- [Docker 公式ドキュメント](https://docs.docker.com/)

### パフォーマンス & 監視
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [OpenTelemetry](https://opentelemetry.io/docs/)
- [Elastic Stack](https://www.elastic.co/guide/)