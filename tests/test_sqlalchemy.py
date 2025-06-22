import pytest
import asyncio
from sqlalchemy import select
from src.database import DatabaseManager
from src.models import User
from src.repositories import UserRepository


@pytest.fixture
async def db_manager():
    """テスト用データベースマネージャー"""
    # テスト用のデータベースURLを使用（本番と異なるDBを使うことを推奨）
    manager = DatabaseManager()
    
    # テスト用のテーブルを作成
    await manager.create_tables()
    
    yield manager
    
    # テスト後のクリーンアップ
    await manager.drop_tables()
    await manager.close()


@pytest.fixture
async def session(db_manager):
    """テスト用セッション"""
    async with db_manager.get_session() as session:
        yield session


@pytest.fixture
async def user_repository(session):
    """ユーザーリポジトリフィクスチャ"""
    return UserRepository(session)


@pytest.fixture
async def sample_users(session):
    """サンプルユーザーデータを作成"""
    users = [
        User(name="Alice", email="alice@example.com"),
        User(name="Bob", email="bob@example.com"),
        User(name="Charlie", email="charlie@example.com")
    ]
    
    for user in users:
        session.add(user)
    await session.commit()
    
    return users


class TestDatabaseManager:
    """DatabaseManagerのテスト"""
    
    @pytest.mark.asyncio
    async def test_connection_creation(self, db_manager):
        """接続の作成テスト"""
        assert db_manager.engine is not None
        assert db_manager.async_session_maker is not None
    
    @pytest.mark.asyncio
    async def test_session_context_manager(self, db_manager):
        """セッションコンテキストマネージャーのテスト"""
        async with db_manager.get_session() as session:
            assert session is not None
            # セッション内でクエリを実行
            result = await session.execute(select(User))
            users = result.scalars().all()
            assert isinstance(users, list)


class TestUserRepository:
    """UserRepositoryのテスト"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, user_repository):
        """ユーザー作成テスト"""
        user = await user_repository.create("Test User", "test@example.com")
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.created_at is not None
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, user_repository, sample_users):
        """全ユーザー取得テスト"""
        users = await user_repository.get_all()
        
        assert len(users) == 3
        emails = [user.email for user in users]
        assert "alice@example.com" in emails
        assert "bob@example.com" in emails
        assert "charlie@example.com" in emails
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_repository, sample_users):
        """ID指定でのユーザー取得テスト"""
        # 存在するユーザー
        user = await user_repository.get_by_id(sample_users[0].id)
        assert user is not None
        assert user.name == "Alice"
        assert user.email == "alice@example.com"
        
        # 存在しないユーザー
        user = await user_repository.get_by_id(9999)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_repository, sample_users):
        """メールアドレスでのユーザー取得テスト"""
        user = await user_repository.get_by_email("bob@example.com")
        assert user is not None
        assert user.name == "Bob"
        
        # 存在しないメールアドレス
        user = await user_repository.get_by_email("nonexistent@example.com")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_update_user(self, user_repository):
        """ユーザー更新テスト"""
        # ユーザーを作成
        user = await user_repository.create("Original Name", "original@example.com")
        user_id = user.id
        
        # 名前を更新
        updated_user = await user_repository.update(user_id, name="Updated Name")
        assert updated_user.name == "Updated Name"
        assert updated_user.email == "original@example.com"
        
        # メールアドレスを更新
        updated_user = await user_repository.update(user_id, email="updated@example.com")
        assert updated_user.name == "Updated Name"
        assert updated_user.email == "updated@example.com"
        
        # 両方を更新
        updated_user = await user_repository.update(
            user_id, 
            name="Final Name", 
            email="final@example.com"
        )
        assert updated_user.name == "Final Name"
        assert updated_user.email == "final@example.com"
    
    @pytest.mark.asyncio
    async def test_delete_user(self, user_repository):
        """ユーザー削除テスト"""
        # ユーザーを作成
        user = await user_repository.create("Delete Me", "delete@example.com")
        user_id = user.id
        
        # 削除前の確認
        assert await user_repository.exists(user_id) is True
        
        # ユーザーを削除
        deleted = await user_repository.delete(user_id)
        assert deleted is True
        
        # 削除後の確認
        assert await user_repository.exists(user_id) is False
        user = await user_repository.get_by_id(user_id)
        assert user is None
        
        # 存在しないユーザーの削除
        deleted = await user_repository.delete(9999)
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_count_users(self, user_repository, sample_users):
        """ユーザー数カウントテスト"""
        count = await user_repository.count()
        assert count == 3
        
        # ユーザーを追加
        await user_repository.create("New User", "new@example.com")
        count = await user_repository.count()
        assert count == 4
    
    @pytest.mark.asyncio
    async def test_user_exists(self, user_repository, sample_users):
        """ユーザー存在確認テスト"""
        # 存在するユーザー
        exists = await user_repository.exists(sample_users[0].id)
        assert exists is True
        
        # 存在しないユーザー
        exists = await user_repository.exists(9999)
        assert exists is False


class TestConcurrentOperations:
    """並行処理のテスト"""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, db_manager):
        """複数ユーザーの同時作成テスト"""
        async def create_user(index: int):
            async with db_manager.get_session() as session:
                repo = UserRepository(session)
                return await repo.create(f"Concurrent {index}", f"concurrent{index}@example.com")
        
        # 10人のユーザーを同時に作成
        tasks = [create_user(i) for i in range(10)]
        users = await asyncio.gather(*tasks)
        
        assert len(users) == 10
        assert all(user.id is not None for user in users)
        
        # 作成されたユーザーを確認
        async with db_manager.get_session() as session:
            repo = UserRepository(session)
            total_count = await repo.count()
            assert total_count == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_read_write(self, db_manager):
        """読み書きの並行処理テスト"""
        # 初期ユーザーを作成
        async with db_manager.get_session() as session:
            repo = UserRepository(session)
            initial_user = await repo.create("Initial User", "initial@example.com")
            initial_id = initial_user.id
        
        async def read_user():
            async with db_manager.get_session() as session:
                repo = UserRepository(session)
                return await repo.get_by_id(initial_id)
        
        async def write_user(index: int):
            async with db_manager.get_session() as session:
                repo = UserRepository(session)
                return await repo.create(f"Writer {index}", f"writer{index}@example.com")
        
        # 読み込みと書き込みを同時実行
        read_tasks = [read_user() for _ in range(5)]
        write_tasks = [write_user(i) for i in range(5)]
        
        results = await asyncio.gather(*read_tasks, *write_tasks)
        
        # 読み込み結果の確認
        read_results = results[:5]
        assert all(user.id == initial_id for user in read_results)
        
        # 書き込み結果の確認
        write_results = results[5:]
        assert len(write_results) == 5
        assert all(user.id is not None for user in write_results)


class TestTransactions:
    """トランザクションのテスト"""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_manager):
        """トランザクションのロールバックテスト"""
        try:
            async with db_manager.get_session() as session:
                repo = UserRepository(session)
                
                # ユーザーを作成
                user1 = await repo.create("Transaction Test 1", "trans1@example.com")
                assert user1.id is not None
                
                # 重複するメールアドレスで意図的にエラーを起こす
                await repo.create("Transaction Test 2", "trans1@example.com")
                
        except Exception:
            # エラーが発生することを期待
            pass
        
        # ロールバックされているので、最初のユーザーも存在しないはず
        async with db_manager.get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_email("trans1@example.com")
            assert user is None
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self, db_manager):
        """トランザクションのコミットテスト"""
        async with db_manager.get_session() as session:
            repo = UserRepository(session)
            
            # 複数のユーザーを作成
            user1 = await repo.create("Commit Test 1", "commit1@example.com")
            user2 = await repo.create("Commit Test 2", "commit2@example.com")
            
            # セッションが自動的にコミットされる
        
        # コミット後の確認
        async with db_manager.get_session() as session:
            repo = UserRepository(session)
            assert await repo.get_by_email("commit1@example.com") is not None
            assert await repo.get_by_email("commit2@example.com") is not None