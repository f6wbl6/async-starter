import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import app
from src.database import db_manager
from src.models import User
from src.dependencies import get_db


# テスト用のデータベースセッションを作成
@pytest.fixture
async def test_db():
    """テスト用データベースセッション"""
    # テスト用のテーブルを作成
    await db_manager.create_tables()
    
    async with db_manager.get_session() as session:
        yield session
    
    # テスト後のクリーンアップ
    await db_manager.drop_tables()


# 依存性のオーバーライド
@pytest.fixture
async def client(test_db):
    """テスト用クライアント"""
    # 依存性を上書き
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # クリーンアップ
    app.dependency_overrides.clear()


# サンプルユーザーデータ
@pytest.fixture
async def sample_user(test_db: AsyncSession):
    """テスト用ユーザーを作成"""
    user = User(name="Test User", email="test@example.com")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


class TestHealthCheck:
    """ヘルスチェックエンドポイントのテスト"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """ヘルスチェックが正常に動作すること"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "version" in data


class TestUserEndpoints:
    """ユーザーエンドポイントのテスト"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, client):
        """ユーザー作成のテスト"""
        user_data = {
            "name": "New User",
            "email": "newuser@example.com"
        }
        response = await client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, client, sample_user):
        """重複するメールアドレスでユーザー作成を試みる"""
        user_data = {
            "name": "Another User",
            "email": sample_user.email  # 既存のメールアドレス
        }
        response = await client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 400
        assert "Email already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_users(self, client, sample_user):
        """ユーザー一覧取得のテスト"""
        response = await client.get("/api/v1/users")
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["users"]) >= 1
        assert data["total"] >= 1
    
    @pytest.mark.asyncio
    async def test_get_users_pagination(self, client):
        """ページネーションのテスト"""
        # 複数ユーザーを作成
        for i in range(5):
            await client.post(
                "/api/v1/users",
                json={"name": f"User {i}", "email": f"user{i}@example.com"}
            )
        
        # 2ページ目を取得
        response = await client.get("/api/v1/users?page=2&per_page=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 2
        assert len(data["users"]) <= 2
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client, sample_user):
        """特定のユーザー取得のテスト"""
        response = await client.get(f"/api/v1/users/{sample_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["name"] == sample_user.name
        assert data["email"] == sample_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client):
        """存在しないユーザーの取得"""
        response = await client.get("/api/v1/users/9999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_user(self, client, sample_user):
        """ユーザー更新のテスト"""
        update_data = {"name": "Updated Name"}
        response = await client.patch(
            f"/api/v1/users/{sample_user.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["name"] == update_data["name"]
        assert data["email"] == sample_user.email  # メールは変更されない
    
    @pytest.mark.asyncio
    async def test_update_user_email(self, client, sample_user):
        """ユーザーのメールアドレス更新のテスト"""
        update_data = {"email": "updated@example.com"}
        response = await client.patch(
            f"/api/v1/users/{sample_user.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == update_data["email"]
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client):
        """存在しないユーザーの更新"""
        update_data = {"name": "Updated Name"}
        response = await client.patch("/api/v1/users/9999", json=update_data)
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_user(self, client, sample_user):
        """ユーザー削除のテスト"""
        response = await client.delete(f"/api/v1/users/{sample_user.id}")
        
        assert response.status_code == 204
        
        # 削除されたことを確認
        get_response = await client.get(f"/api/v1/users/{sample_user.id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client):
        """存在しないユーザーの削除"""
        response = await client.delete("/api/v1/users/9999")
        
        assert response.status_code == 404


class TestValidation:
    """バリデーションのテスト"""
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, client):
        """無効なメールアドレスでユーザー作成"""
        user_data = {
            "name": "Test User",
            "email": "invalid-email"  # 無効なメール形式
        }
        response = await client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 422  # Validation Error
    
    @pytest.mark.asyncio
    async def test_create_user_empty_name(self, client):
        """空の名前でユーザー作成"""
        user_data = {
            "name": "",  # 空文字
            "email": "test@example.com"
        }
        response = await client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 422  # Validation Error
    
    @pytest.mark.asyncio
    async def test_update_user_no_fields(self, client, sample_user):
        """更新フィールドなしでユーザー更新"""
        response = await client.patch(
            f"/api/v1/users/{sample_user.id}",
            json={}
        )
        
        assert response.status_code == 400
        assert "No fields to update" in response.json()["detail"]


class TestConcurrency:
    """並行処理のテスト"""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, client):
        """並行してユーザーを作成"""
        import asyncio
        
        async def create_user(index: int):
            user_data = {
                "name": f"Concurrent User {index}",
                "email": f"concurrent{index}@example.com"
            }
            return await client.post("/api/v1/users", json=user_data)
        
        # 10人のユーザーを並行作成
        tasks = [create_user(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # すべて成功することを確認
        for response in responses:
            assert response.status_code == 201
        
        # ユーザー数を確認
        list_response = await client.get("/api/v1/users")
        assert list_response.json()["total"] >= 10