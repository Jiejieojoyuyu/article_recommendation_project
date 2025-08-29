"""
用户认证API接口
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models.user import UserCreate, UserLogin, User, UserPublic, Token, UserUpdate
from ..core.security import (
    verify_password, get_password_hash, create_access_token, 
    verify_token, validate_password_strength
)
from ..db.database import user_manager

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()

@router.post("/register", response_model=UserPublic, summary="用户注册")
async def register_user(user_data: UserCreate):
    """
    用户注册
    
    - **username**: 用户名（唯一）
    - **email**: 邮箱地址
    - **password**: 密码
    - **full_name**: 全名
    - **affiliation**: 所属机构（可选）
    - **research_interests**: 研究兴趣列表（可选）
    """
    # 检查用户名是否已存在
    existing_user = await user_manager.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已被使用
    existing_email_user = await user_manager.get_user_by_email(user_data.email)
    if existing_email_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 验证密码强度
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    new_user_data = user_data.model_dump()
    new_user_data["password_hash"] = hashed_password
    del new_user_data["password"]  # 删除明文密码
    
    created_user = await user_manager.create_user(new_user_data)
    
    return UserPublic(**created_user)

@router.post("/login", response_model=Token, summary="用户登录")
async def login(user_credentials: UserLogin):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回JWT访问令牌
    """
    # 验证用户凭据
    user = await user_manager.get_user_by_username(user_credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    # 更新最后登录时间
    from datetime import datetime
    await user_manager.update_last_login(user["id"])
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    获取当前登录用户
    """
    token = credentials.credentials
    payload = verify_token(token)
    username = payload.get("sub")
    
    user = await user_manager.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return User(**user)

@router.get("/me", response_model=UserPublic, summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的个人信息
    """
    return UserPublic(**current_user.model_dump())

@router.put("/me", response_model=UserPublic, summary="更新用户信息")
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户的个人信息
    
    - **full_name**: 全名
    - **affiliation**: 所属机构
    - **research_interests**: 研究兴趣列表
    - **email**: 邮箱地址
    """
    # 检查邮箱是否已被其他用户使用
    if user_update.email:
        existing_email_user = await user_manager.get_user_by_email(user_update.email)
        if existing_email_user and existing_email_user["id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
    
    # 更新用户信息
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = await user_manager.update_user(current_user.id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserPublic(**updated_user)

@router.post("/change-password", summary="修改密码")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user)
):
    """
    修改用户密码
    
    - **current_password**: 当前密码
    - **new_password**: 新密码
    """
    # 验证当前密码
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 验证新密码强度
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # 更新密码
    new_password_hash = get_password_hash(new_password)
    await user_manager.update_user(current_user.id, {"password_hash": new_password_hash})
    
    return {"message": "密码修改成功"}

@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出（客户端需要删除本地存储的token）
    """
    return {"message": "登出成功"}

@router.get("/validate-token", summary="验证令牌")
async def validate_token(current_user: User = Depends(get_current_user)):
    """
    验证JWT令牌是否有效
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username
    }

@router.delete("/delete-account", summary="删除账户")
async def delete_account(
    password: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除用户账户（需要密码确认）
    
    - **password**: 当前密码用于确认
    """
    # 验证密码
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码错误"
        )
    
    # TODO: 实现从数据库中删除用户
    # 暂时禁用删除功能，因为需要在UserManager中实现delete_user方法
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="删除账户功能暂时不可用"
    )

# 依赖函数，供其他模块使用
def get_current_user_dependency():
    """
    获取当前用户的依赖函数，供其他路由使用
    """
    return Depends(get_current_user)

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[User]:
    """
    获取当前登录用户（可选）
    如果没有提供认证凭据，返回None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        username = payload.get("sub")
        
        user = await user_manager.get_user_by_username(username)
        if user is None:
            return None
            
        return User(**user)
    except:
        return None

