# Python非同期データベース処理の学習プロジェクト

このプロジェクトは、Python 3.11での非同期データベース処理を学習するためのサンプルコードです。SQLAlchemy 2.0の最新機能とaiomysqlを使用して、モダンな非同期ORMの実装パターンを示しています。

## 技術スタック

### コア技術
- **Python 3.11** - 最新の言語機能とパフォーマンス改善
- **MySQL 8.0** - プロダクショングレードのデータベース
- **SQLAlchemy 2.0** - 最新の非同期ORM（Mapped型注釈サポート）
- **aiomysql** - 非同期MySQLドライバー
- **FastAPI** - 高速な非同期Webフレームワーク
- **Pydantic v2** - 最新のデータバリデーション（Annotated型サポート）

### 開発ツール
- **uv** - 高速Pythonパッケージマネージャー
- **pytest + pytest-asyncio** - 非同期テストフレームワーク
- **python-dotenv** - 環境変数管理

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

### 4. テストの実行

```bash
# 仮想環境を有効化
source .venv/bin/activate

# テスト実行
pytest tests/test_sqlalchemy.py
```

## 非同期処理の解説

### 1. 非同期処理とは

非同期処理は、I/O待機時間を有効活用するプログラミング手法です。データベースアクセスのような時間のかかる処理を待っている間、他のタスクを実行できます。

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

このクラスはSQLAlchemyの非同期セッションを管理します：

- **非同期エンジン**: `create_async_engine()`で非同期対応のエンジンを作成
- **セッションファクトリ**: `async_sessionmaker()`でセッション生成を管理
- **コンテキストマネージャー**: `get_session()`で自動的にセッションを管理

#### モデル定義の例（SQLAlchemy 2.0スタイル）

```python
from datetime import datetime, timezone
from sqlalchemy import String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """SQLAlchemyベースクラス"""
    pass

class User(Base):
    """
    ユーザーモデル
    
    SQLAlchemy 2.0の最新機能を使用:
    - Mapped型注釈による型安全性
    - mapped_column()による現代的なカラム定義
    - server_defaultとdefault_factoryの併用
    """
    __tablename__ = "users"
    
    # SQLAlchemy 2.0スタイルの型ヒント付きマッピング
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        default_factory=lambda: datetime.now(timezone.utc)
    )
```

**SQLAlchemy 2.0の改善点**:
- `Mapped[型]` による明示的な型定義
- `mapped_column()` による統一されたカラム定義
- サーバーサイドとクライアントサイドのデフォルト値の併用
- インデックスの明示的な定義

#### リポジトリパターンの実装（SQLAlchemy 2.0スタイル）

```python
from typing import Optional, Sequence
from sqlalchemy import select, update, delete, exists, func
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository:
    """
    ユーザーリポジトリ
    
    SQLAlchemy 2.0スタイルのクエリを使用したデータアクセスレイヤー
    """
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """IDでユーザーを取得"""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_paginated(self, offset: int = 0, limit: int = 20) -> Sequence[User]:
        """ページネーション付きでユーザーを取得"""
        stmt = (
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update(
        self, 
        user_id: int, 
        name: Optional[str] = None, 
        email: Optional[str] = None
    ) -> Optional[User]:
        """ユーザー情報を更新（SQLAlchemy 2.0 RETURNING文使用）"""
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if email is not None:
            update_data['email'] = email
        
        if not update_data:
            return await self.get_by_id(user_id)
        
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)  # SQLAlchemy 2.0の新機能
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()
```

**SQLAlchemy 2.0の重要なポイント**:
- `select()`, `update()`, `delete()` 関数による統一されたクエリ構築
- `.returning()` 句による効率的な更新結果取得
- `Sequence[Model]` による型安全なコレクション戻り値
- 明示的な型注釈による IDE サポート向上

### 3. 非同期処理のメリット

#### 並行処理の実装例

```python
# 複数のユーザーを同時に作成
async def create_concurrent_user(index: int):
    async with db_manager.get_session() as session:
        repo = UserRepository(session)
        return await repo.create(f'User {index}', f'user{index}@example.com')

tasks = [create_concurrent_user(i) for i in range(5)]
users = await asyncio.gather(*tasks)
```

この例では：
- 5つのINSERT操作が並行して実行されます
- 各操作は独立したセッションで実行されます
- SQLAlchemyが自動的にトランザクションを管理します
- `asyncio.gather()`で複数の非同期タスクを同時実行

### 4. テストの書き方（最新パターン）

pytest-asyncioを使用した非同期テストの例：

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import db_manager
from src.repositories import UserRepository
from src.models import User

@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """テスト用データベースセッション"""
    # テーブル作成
    await db_manager.create_tables()
    
    # セッション提供
    async with db_manager.get_session() as session:
        yield session
        # 自動的にロールバック（テスト分離）
        await session.rollback()
    
    # テーブル削除
    await db_manager.drop_tables()

@pytest_asyncio.fixture
async def user_repository(db_session: AsyncSession) -> UserRepository:
    """ユーザーリポジトリフィクスチャ"""
    return UserRepository(db_session)

@pytest.mark.asyncio
async def test_create_user(user_repository: UserRepository):
    """ユーザー作成テスト"""
    # 作成
    user = await user_repository.create("Test User", "test@example.com")
    
    # 検証
    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.created_at is not None

@pytest.mark.asyncio
async def test_get_paginated_users(user_repository: UserRepository):
    """ページネーションテスト"""
    # テストデータ作成
    for i in range(25):
        await user_repository.create(f"User {i}", f"user{i}@example.com")
    
    # ページネーション取得
    users = await user_repository.get_paginated(offset=0, limit=10)
    
    # 検証
    assert len(users) == 10
    # 作成日時の降順で並んでいることを確認
    for i in range(1, len(users)):
        assert users[i-1].created_at >= users[i].created_at
```

**現代的なテストのポイント**:
- `@pytest_asyncio.fixture` による非同期フィクスチャ
- 型注釈による IDE サポート向上
- テスト分離のための適切なセットアップ/ティアダウン
- SQLAlchemy 2.0 の機能を活用したテストデータ操作

### 5. エラーハンドリングとトランザクション

```python
@asynccontextmanager
async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
    async with self.async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

SQLAlchemyでのトランザクション管理：
- コンテキストマネージャーが自動的にトランザクションを管理
- エラー時は自動的にロールバック
- 正常終了時は自動的にコミット
- `expire_on_commit=False`で、コミット後もオブジェクトにアクセス可能

## プロジェクト構造（リファクタリング後）

```
async-starter/
├── compose.yaml             # Docker Compose設定
├── init.sql                # 初期データベース構造
├── pyproject.toml          # Python・uv プロジェクト設定
├── pytest.ini              # pytest設定
├── gunicorn.conf.py        # 本番環境用Gunicorn設定
├── start.sh                # アプリケーション起動スクリプト
├── run.py                  # アプリケーションエントリーポイント
├── .env.example            # 環境変数の例
├── src/
│   ├── __init__.py        # パッケージ初期化
│   ├── app.py             # FastAPIアプリケーション設定
│   ├── config.py          # Pydantic設定管理
│   ├── database.py        # データベース接続管理
│   ├── dependencies.py   # FastAPI依存性注入
│   ├── middleware.py      # カスタムミドルウェア
│   ├── models.py          # SQLAlchemy 2.0モデル
│   ├── repositories.py    # リポジトリクラス
│   ├── schemas.py         # Pydantic v2 スキーマ
│   ├── routers/           # APIルーター
│   │   ├── __init__.py   
│   │   ├── health.py     # ヘルスチェックAPI
│   │   └── users.py      # ユーザー管理API
│   └── services/          # ビジネスロジック
│       ├── __init__.py   
│       └── user_service.py # ユーザーサービス
├── tests/
│   ├── __init__.py       
│   ├── test_api.py       # FastAPI エンドポイントテスト
│   ├── test_config.py    # 設定テスト
│   ├── test_models.py    # SQLAlchemyモデルテスト
│   ├── test_repositories.py # リポジトリテスト
│   └── test_services.py  # サービステスト
├── async_db_guide.md     # 非同期DB学習ガイド（このファイル）
└── FASTAPI_GUIDE.md      # FastAPI実装ガイド
```

**アーキテクチャの改善点**:
- **レイヤー分離**: API層、サービス層、リポジトリ層の明確な分離
- **機能別ディレクトリ**: ルーターとサービスの機能別整理
- **設定の一元化**: Pydantic BaseSettings による型安全な設定管理
- **依存性注入**: FastAPI の DI システム活用
- **ミドルウェア**: ログ、レート制限、DB監視の統合

## 注意事項とベストプラクティス

### 1. セキュリティ
- **環境変数の管理**: 本番環境では必ず環境変数でDB認証情報を管理
- **設定の検証**: Pydantic による実行時設定バリデーション
- **SQL インジェクション対策**: SQLAlchemy のパラメータ化クエリを使用

### 2. パフォーマンス
- **セッションの管理**: セッションは必ずコンテキストマネージャーで管理
- **並行処理**: 各非同期タスクは独立したセッションを使用
- **接続プール**: 適切なプールサイズ設定による効率化
- **インデックス**: 頻繁に検索されるカラムへのインデックス追加

### 3. 開発効率
- **型安全性**: SQLAlchemy 2.0 Mapped型 + Pydantic v2 による完全な型サポート
- **docstring**: 包括的なドキュメンテーション
- **テスト分離**: 各テストは独立したデータベース状態で実行

### 4. 運用
- **マイグレーション**: 本番環境では Alembic で DB マイグレーションを管理
- **ログ**: 構造化ログによる運用監視
- **ヘルスチェック**: `/health` エンドポイントによる死活監視
- **メトリクス**: リクエスト処理時間、DB接続プール状態の監視

### 5. 最新技術の活用
- **SQLAlchemy 2.0**: `Mapped[型]` と `mapped_column()` の使用
- **Pydantic v2**: `Annotated` 型と `Field()` による高度なバリデーション
- **FastAPI**: 非同期処理とOpenAPI自動生成の活用
- **Python 3.11**: 最新の言語機能とパフォーマンス改善の活用

## 参考リンク

### SQLAlchemy 2.0
- [SQLAlchemy 2.0 非同期ドキュメント](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [SQLAlchemy 2.0 マイグレーションガイド](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [Mapped 型注釈ガイド](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#mapped-class-essential-components)

### FastAPI
- [FastAPI 公式ドキュメント](https://fastapi.tiangolo.com/)
- [FastAPI 非同期データベース](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [FastAPI 依存性注入](https://fastapi.tiangolo.com/tutorial/dependencies/)

### Pydantic v2
- [Pydantic v2 公式ドキュメント](https://docs.pydantic.dev/2.0/)
- [Pydantic Settings](https://docs.pydantic.dev/2.0/usage/pydantic_settings/)
- [Annotated フィールド](https://docs.pydantic.dev/2.0/usage/annotated/)

### ツール・ライブラリ
- [uv 公式ドキュメント](https://github.com/astral-sh/uv)
- [aiomysql 公式ドキュメント](https://aiomysql.readthedocs.io/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

### Python
- [Python 3.11 新機能](https://docs.python.org/3/whatsnew/3.11.html)
- [Python asyncio 公式ドキュメント](https://docs.python.org/3/library/asyncio.html)