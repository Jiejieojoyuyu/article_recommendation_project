"""
用户相关的Pydantic模型
"""
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr
    full_name: str
    affiliation: Optional[str] = None
    research_interests: List[str] = []

class UserCreate(UserBase):
    """创建用户模型"""
    password: str

class UserUpdate(BaseModel):
    """更新用户模型"""
    full_name: Optional[str] = None
    affiliation: Optional[str] = None
    research_interests: Optional[List[str]] = None
    email: Optional[EmailStr] = None

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str

class Folder(BaseModel):
    """收藏夹模型"""
    id: str
    name: str
    parent_id: Optional[str] = None
    papers: List[str] = []
    created_at: str

class FolderCreate(BaseModel):
    """创建收藏夹模型"""
    name: str
    parent_id: Optional[str] = None

class User(UserBase):
    """完整用户模型"""
    id: str
    password_hash: str
    created_at: str
    last_login: Optional[str] = None
    followed_authors: List[str] = []
    bookmarked_papers: List[str] = []
    reading_history: List[str] = []
    folders: List[Folder] = []

    class Config:
        from_attributes = True

class UserPublic(UserBase):
    """公开用户信息模型"""
    id: str
    created_at: str
    last_login: Optional[str] = None

class Token(BaseModel):
    """JWT令牌模型"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None

class UserStats(BaseModel):
    """用户统计信息"""
    total_bookmarks: int
    total_folders: int
    followed_authors_count: int
    reading_history_count: int

class SearchHistory(BaseModel):
    """搜索历史模型"""
    user_id: str
    query: str
    timestamp: str
    results_clicked: List[str] = []

class Recommendation(BaseModel):
    """推荐记录模型"""
    user_id: str
    paper_id: str
    score: float
    reason: str
    created_at: str

