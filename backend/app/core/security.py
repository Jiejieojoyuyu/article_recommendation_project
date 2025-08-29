"""
安全模块：密码处理、JWT token等
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = "your-secret-key-here-change-in-production"  # 生产环境中应该使用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
    
    Returns:
        验证结果
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    获取密码哈希值
    
    Args:
        password: 明文密码
    
    Returns:
        哈希密码
    """
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
    
    Returns:
        JWT令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌
    
    Returns:
        解码后的数据
    
    Raises:
        HTTPException: 令牌无效时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

def get_current_user_id(token: str) -> str:
    """
    从令牌中获取当前用户ID
    
    Args:
        token: JWT令牌
    
    Returns:
        用户ID
    """
    payload = verify_token(token)
    return payload.get("sub")

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建刷新令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
    
    Returns:
        刷新令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # 刷新令牌7天有效
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str) -> Dict[str, Any]:
    """
    验证刷新令牌
    
    Args:
        token: 刷新令牌
    
    Returns:
        解码后的数据
    
    Raises:
        HTTPException: 令牌无效时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type: str = payload.get("type")
        username: str = payload.get("sub")
        
        if username is None or token_type != "refresh":
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度（宽松版本）
    
    Args:
        password: 要验证的密码
    
    Returns:
        (是否有效, 错误消息)
    """
    if len(password) < 3:
        return False, "密码长度至少3位"
    
    return True, ""

def generate_api_key() -> str:
    """
    生成API密钥
    
    Returns:
        API密钥
    """
    import secrets
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """
    哈希API密钥
    
    Args:
        api_key: API密钥
    
    Returns:
        哈希后的API密钥
    """
    return get_password_hash(api_key)

def verify_api_key(api_key: str, hashed_api_key: str) -> bool:
    """
    验证API密钥
    
    Args:
        api_key: 原始API密钥
        hashed_api_key: 哈希后的API密钥
    
    Returns:
        验证结果
    """
    return verify_password(api_key, hashed_api_key)

