"""
ユーザー管理APIルーター

このモジュールはユーザーのCRUD操作を提供するREST APIエンドポイントを定義します。
ユーザーの作成、取得、更新、削除機能を含み、ページネーションもサポートします。
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.services.user_service import UserService
from src.schemas import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    UserListResponse
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりの表示数"),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザー一覧を取得
    
    ページネーション機能付きでユーザー一覧を取得します。
    作成日時の降順で並び替えられます。
    
    Args:
        page: ページ番号（1以上）
        per_page: 1ページあたりの表示数（1-100）
        db: データベースセッション（依存性注入）
        
    Returns:
        UserListResponse: ユーザー一覧とページネーション情報
        
    Raises:
        HTTPException: データベースエラーやバリデーションエラー
        
    Note:
        - デフォルトは1ページ目、20件表示
        - 最大100件まで一度に取得可能
        - total_pagesプロパティで総ページ数を計算可能
    """
    service = UserService(db)
    users, total = await service.get_users(page, per_page)
    
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    特定のユーザーを取得
    
    ユーザーIDを指定して、個別のユーザー情報を取得します。
    
    Args:
        user_id: 取得するユーザーのID
        db: データベースセッション（依存性注入）
        
    Returns:
        UserResponse: ユーザー情報
        
    Raises:
        HTTPException: ユーザーが見つからない場合（404 Not Found）
    """
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    新規ユーザーを作成
    
    ユーザー情報を受け取り、新しいユーザーをデータベースに作成します。
    メールアドレスはユニーク制約があります。
    
    Args:
        user_data: 作成するユーザーの情報
        db: データベースセッション（依存性注入）
        
    Returns:
        UserResponse: 作成されたユーザー情報（IDと作成日時を含む）
        
    Raises:
        HTTPException: 
            - バリデーションエラー（400 Bad Request）
            - メールアドレス重複エラー（400 Bad Request）
            
    Note:
        作成日時は自動的に設定されます（UTC）
    """
    service = UserService(db)
    
    try:
        user = await service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザー情報を更新
    
    指定されたユーザーIDのユーザー情報を部分的に更新します。
    指定されたフィールドのみが更新され、未指定のフィールドは変更されません。
    
    Args:
        user_id: 更新するユーザーのID
        user_data: 更新するユーザー情報（部分更新可能）
        db: データベースセッション（依存性注入）
        
    Returns:
        UserResponse: 更新されたユーザー情報
        
    Raises:
        HTTPException:
            - ユーザーが見つからない場合（404 Not Found）
            - バリデーションエラー（400 Bad Request）
            - メールアドレス重複エラー（400 Bad Request）
            
    Note:
        PATCHメソッドによる部分更新をサポート。
        空のリクエストボディは400エラーを返します。
    """
    service = UserService(db)
    
    try:
        user = await service.update_user(user_id, user_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザーを削除
    
    指定されたユーザーIDのユーザーをデータベースから完全に削除します。
    削除は取り消しできない操作です。
    
    Args:
        user_id: 削除するユーザーのID
        db: データベースセッション（依存性注入）
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException: ユーザーが見つからない場合（404 Not Found）
        
    Warning:
        この操作は元に戻せません。本番環境では論理削除の使用を検討してください。
        
    Note:
        成功時は204 No Contentステータスを返し、レスポンスボディは空です。
    """
    service = UserService(db)
    deleted = await service.delete_user(user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return None