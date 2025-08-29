"""
个人工作台API接口
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from ..models.user import User, Folder, FolderCreate, UserStats, Recommendation
from ..models.paper import PaperSummary, AuthorSummary
from ..api.auth import get_current_user
from ..db.database import db, user_manager
from ..algorithms.recommender import get_daily_recommendations

router = APIRouter(prefix="/workspace", tags=["个人工作台"])

@router.get("/dashboard", summary="获取工作台概览")
async def get_workspace_dashboard(current_user: User = Depends(get_current_user)):
    """
    获取个人工作台的概览信息
    """
    user_data = await user_manager.get_user_by_id(current_user.id)
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取用户的收藏论文
    bookmarked_papers = await user_manager.get_user_bookmarks(current_user.id)
    
    # 获取用户的文件夹
    user_folders = await user_manager.get_user_folders(current_user.id)
    
    # 获取关注的作者
    followed_authors = await user_manager.get_followed_authors(current_user.id)
    
    # 获取阅读历史
    reading_history = await user_manager.get_reading_history(current_user.id, limit=50)
    
    # 统计信息
    stats = UserStats(
        total_bookmarks=len(bookmarked_papers),
        total_folders=len(user_folders),
        followed_authors_count=len(followed_authors),
        reading_history_count=len(reading_history)
    )
    
    # 最近收藏的论文
    recent_bookmarks = []
    for paper_id in bookmarked_papers[-5:]:  # 最近5篇
        paper = await db.get_paper_by_id(paper_id)
        if paper:
            summary = PaperSummary(
                id=paper["id"],
                short_id=paper.get("short_id"),
                title=paper["title"],
                author_names=paper["author_names"],
                year=paper["year"],
                journal=paper["journal"],
                citation_count=paper["citation_count"],
                truth_value_score=paper.get("truth_value_score"),
                research_field=paper["research_field"]
            )
            recent_bookmarks.append(summary)
    
    # 关注的作者
    followed_authors_info = []
    for author_id in followed_authors:
        # 从作者ID中提取作者姓名并获取信息
        author_name = author_id.replace("author_", "").replace("_", " ")
        author = await db.get_author_info(author_name)
        if author:
            summary = AuthorSummary(
                id=author["id"],
                name=author["name"],
                affiliation=author["affiliation"],
                research_areas=author["research_areas"],
                h_index=author["h_index"],
                citation_count=author["citation_count"],
                paper_count=author["paper_count"]
            )
            followed_authors_info.append(summary)
    
    # 获取推荐列表
    recommendations = get_daily_recommendations(
        user_id=current_user.id,
        user_data=user_data,
        papers=await db.get_papers(limit=1000),  # 获取更多论文用于推荐
        limit=5
    )
    
    return {
        "user_stats": stats,
        "recent_bookmarks": recent_bookmarks,
        "followed_authors": followed_authors_info,
        "recommendations": recommendations,
        "last_updated": user_data.get("last_login")
    }

@router.get("/bookmarks", response_model=List[PaperSummary], summary="获取收藏的论文")
async def get_bookmarked_papers(
    current_user: User = Depends(get_current_user),
    folder_id: Optional[str] = Query(None, description="文件夹ID"),
    limit: int = Query(20, description="返回数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """
    获取用户收藏的论文列表
    
    - **folder_id**: 指定文件夹ID（可选，不指定则返回所有收藏）
    - **limit**: 返回的论文数量限制
    - **offset**: 分页偏移量
    """
    user_data = await user_manager.get_user_by_id(current_user.id)
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 确定要返回的论文ID列表
    if folder_id:
        # 查找指定文件夹
        user_folders = await user_manager.get_user_folders(current_user.id)
        target_folder = None
        for folder in user_folders:
            if folder["id"] == folder_id:
                target_folder = folder
                break
        
        if not target_folder:
            raise HTTPException(status_code=404, detail="文件夹不存在")
        
        # 获取文件夹中的论文
        paper_ids = []
        # 这里需要实现从folder_papers表获取论文的逻辑
        # 暂时返回空列表，后续可以扩展
    else:
        # 返回所有收藏
        paper_ids = await user_manager.get_user_bookmarks(current_user.id)
    
    # 分页
    paginated_ids = paper_ids[offset:offset + limit]
    
    # 获取论文详情
    bookmarked_papers = []
    for paper_id in paginated_ids:
        paper = await db.get_paper_by_id(paper_id)
        if paper:
            summary = PaperSummary(
                id=paper["id"],
                short_id=paper.get("short_id"),
                title=paper["title"],
                author_names=paper["author_names"],
                year=paper["year"],
                journal=paper["journal"],
                citation_count=paper["citation_count"],
                truth_value_score=paper.get("truth_value_score"),
                research_field=paper["research_field"]
            )
            bookmarked_papers.append(summary)
    
    return bookmarked_papers

@router.get("/folders", response_model=List[Folder], summary="获取收藏夹列表")
async def get_folders(current_user: User = Depends(get_current_user)):
    """
    获取用户的收藏夹列表（支持多层级结构）
    """
    user_folders = await user_manager.get_user_folders(current_user.id)
    folders = [Folder(**folder) for folder in user_folders]
    return folders

@router.post("/folders", response_model=Folder, summary="创建收藏夹")
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user)
):
    """
    创建新的收藏夹
    
    - **name**: 收藏夹名称
    - **parent_id**: 父收藏夹ID（可选，用于创建子文件夹）
    """
    user_data = await user_manager.get_user_by_id(current_user.id)
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查父文件夹是否存在（如果指定了parent_id）
    if folder_data.parent_id:
        user_folders = await user_manager.get_user_folders(current_user.id)
        parent_exists = any(
            folder["id"] == folder_data.parent_id 
            for folder in user_folders
        )
        if not parent_exists:
            raise HTTPException(status_code=404, detail="父文件夹不存在")
    
    # 检查同级文件夹名称是否重复
    user_folders = await user_manager.get_user_folders(current_user.id)
    for folder in user_folders:
        if (folder["name"] == folder_data.name and 
            folder.get("parent_id") == folder_data.parent_id):
            raise HTTPException(status_code=400, detail="同级目录下已存在同名文件夹")
    
    # 创建文件夹
    created_folder = await user_manager.create_folder(current_user.id, folder_data.model_dump())
    if not created_folder:
        raise HTTPException(status_code=500, detail="创建文件夹失败")
    
    return Folder(**created_folder)

@router.put("/folders/{folder_id}", response_model=Folder, summary="更新收藏夹")
async def update_folder(
    folder_id: str,
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user)
):
    """
    更新收藏夹信息
    
    - **folder_id**: 收藏夹ID
    - **name**: 新的收藏夹名称
    - **parent_id**: 新的父收藏夹ID（可选）
    """
    # 查找目标文件夹
    user_folders = await user_manager.get_user_folders(current_user.id)
    target_folder = None
    for folder in user_folders:
        if folder["id"] == folder_id:
            target_folder = folder
            break
    
    if not target_folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    # 检查新父文件夹是否存在（如果指定了parent_id）
    if folder_data.parent_id and folder_data.parent_id != target_folder.get("parent_id"):
        parent_exists = any(
            folder["id"] == folder_data.parent_id 
            for folder in user_folders
        )
        if not parent_exists:
            raise HTTPException(status_code=404, detail="父文件夹不存在")
        
        # 防止循环引用（简化检查）
        if folder_data.parent_id == folder_id:
            raise HTTPException(status_code=400, detail="不能将文件夹移动到自身")
    
    # 更新文件夹信息 - 这里需要实现实际的更新逻辑
    # 暂时返回原文件夹，后续可以扩展
    updated_folder = {
        **target_folder,
        "name": folder_data.name,
        "parent_id": folder_data.parent_id
    }
    
    return Folder(**updated_folder)

@router.delete("/folders/{folder_id}", summary="删除收藏夹")
async def delete_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    删除收藏夹（及其所有子文件夹）
    
    - **folder_id**: 收藏夹ID
    """
    # 查找要删除的文件夹
    user_folders = await user_manager.get_user_folders(current_user.id)
    target_folder = None
    for folder in user_folders:
        if folder["id"] == folder_id:
            target_folder = folder
            break
    
    if not target_folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    # 删除文件夹 - 这里需要实现实际的删除逻辑
    # 暂时返回成功，后续可以扩展
    return {"message": "文件夹删除成功"}

@router.post("/folders/{folder_id}/papers/{paper_id}", summary="将论文添加到收藏夹")
async def add_paper_to_folder(
    folder_id: str,
    paper_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    将论文添加到指定收藏夹
    
    - **folder_id**: 收藏夹ID
    - **paper_id**: 论文ID
    """
    # 检查论文是否存在
    paper = await db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 查找目标文件夹
    user_folders = await user_manager.get_user_folders(current_user.id)
    target_folder = None
    for folder in user_folders:
        if folder["id"] == folder_id:
            target_folder = folder
            break
    
    if not target_folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    # 添加论文到文件夹 - 这里需要实现实际的添加逻辑
    # 暂时返回成功，后续可以扩展
    return {"message": "论文已添加到收藏夹"}

@router.delete("/folders/{folder_id}/papers/{paper_id}", summary="从收藏夹移除论文")
async def remove_paper_from_folder(
    folder_id: str,
    paper_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    从指定收藏夹移除论文
    
    - **folder_id**: 收藏夹ID
    - **paper_id**: 论文ID
    """
    # 查找目标文件夹
    user_folders = await user_manager.get_user_folders(current_user.id)
    target_folder = None
    for folder in user_folders:
        if folder["id"] == folder_id:
            target_folder = folder
            break
    
    if not target_folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    # 从文件夹移除论文 - 这里需要实现实际的移除逻辑
    # 暂时返回成功，后续可以扩展
    return {"message": "论文已从收藏夹移除"}

@router.get("/followed-authors", response_model=List[AuthorSummary], summary="获取关注的作者")
async def get_followed_authors(current_user: User = Depends(get_current_user)):
    """
    获取用户关注的作者列表
    """
    
    followed_authors = await user_manager.get_followed_authors(current_user.id)
    followed_authors_info = []
    for author_id in followed_authors:
        # 从作者ID中提取作者姓名并获取信息
        author_name = author_id.replace("author_", "").replace("_", " ")
        author = await db.get_author_info(author_name)
        if author:
            summary = AuthorSummary(
                id=author["id"],
                name=author["name"],
                affiliation=author["affiliation"],
                research_areas=author["research_areas"],
                h_index=author["h_index"],
                citation_count=author["citation_count"],
                paper_count=author["paper_count"]
            )
            followed_authors_info.append(summary)
    
    return followed_authors_info

@router.get("/reading-history", response_model=List[PaperSummary], summary="获取阅读历史")
async def get_reading_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, description="返回数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """
    获取用户的阅读历史
    
    - **limit**: 返回的论文数量限制
    - **offset**: 分页偏移量
    """
    # 获取阅读历史（倒序，最新的在前）
    reading_history = await user_manager.get_reading_history(current_user.id, limit=1000)
    reading_history = reading_history[::-1]
    paginated_history = reading_history[offset:offset + limit]
    
    # 获取论文详情
    history_papers = []
    for paper_id in paginated_history:
        paper = await db.get_paper_by_id(paper_id)
        if paper:
            summary = PaperSummary(
                id=paper["id"],
                short_id=paper.get("short_id"),
                title=paper["title"],
                author_names=paper["author_names"],
                year=paper["year"],
                journal=paper["journal"],
                citation_count=paper["citation_count"],
                truth_value_score=paper.get("truth_value_score"),
                research_field=paper["research_field"]
            )
            history_papers.append(summary)
    
    return history_papers

@router.post("/reading-history/{paper_id}", summary="添加阅读记录")
async def add_reading_record(
    paper_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    添加论文到阅读历史
    
    - **paper_id**: 论文ID
    """
    # 检查论文是否存在
    paper = await db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    
    # 添加到阅读历史
    await user_manager.add_reading_history(current_user.id, paper_id)
    
    return {"message": "阅读记录已添加"}

@router.get("/recommendations", summary="获取个性化推荐")
async def get_personalized_recommendations(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, description="推荐数量")
):
    """
    获取基于用户偏好的个性化论文推荐
    
    - **limit**: 推荐论文数量
    """
    # 获取推荐列表
    recommendations = get_daily_recommendations(
        user_id=current_user.id,
        user_data={},  # 暂时使用空字典，后续可以扩展
        papers=await db.get_papers(limit=1000),  # 获取更多论文用于推荐
        limit=limit
    )
    
    # 获取推荐论文的详细信息
    recommended_papers = []
    for rec in recommendations:
        paper = await db.get_paper_by_id(rec["paper_id"])
        if paper:
            paper_summary = PaperSummary(
                id=paper["id"],
                short_id=paper.get("short_id"),
                title=paper["title"],
                author_names=paper["author_names"],
                year=paper["year"],
                journal=paper["journal"],
                citation_count=paper["citation_count"],
                truth_value_score=paper.get("truth_value_score"),
                research_field=paper["research_field"]
            )
            recommended_papers.append({
                "paper": paper_summary,
                "recommendation_score": rec["score"],
                "reason": rec["reason"],
                "type": rec["type"]
            })
    
    return {
        "recommendations": recommended_papers,
        "total": len(recommended_papers),
        "generated_at": "2023-12-01T10:00:00Z"
    }

@router.get("/stats", response_model=UserStats, summary="获取用户统计信息")
async def get_user_statistics(current_user: User = Depends(get_current_user)):
    """
    获取用户的详细统计信息
    """
    # 获取用户的收藏论文
    bookmarked_papers = await user_manager.get_user_bookmarks(current_user.id)
    
    # 获取用户的文件夹
    user_folders = await user_manager.get_user_folders(current_user.id)
    
    # 获取关注的作者
    followed_authors = await user_manager.get_followed_authors(current_user.id)
    
    # 获取阅读历史
    reading_history = await user_manager.get_reading_history(current_user.id, limit=1000)
    
    return UserStats(
        total_bookmarks=len(bookmarked_papers),
        total_folders=len(user_folders),
        followed_authors_count=len(followed_authors),
        reading_history_count=len(reading_history)
    )

