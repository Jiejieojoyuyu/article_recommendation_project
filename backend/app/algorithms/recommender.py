"""
推荐算法模块
提供个性化论文推荐功能
"""
import random
import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict

def get_daily_recommendations(user_id: str, user_data: Dict[str, Any] = None, 
                            papers: List[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    获取用户的每日推荐论文
    
    Args:
        user_id: 用户ID
        user_data: 用户数据（包含兴趣、历史等）
        papers: 论文库
        limit: 推荐数量限制
    
    Returns:
        推荐论文列表，包含推荐分数和理由
    """
    if not papers:
        # 模拟推荐数据
        return generate_mock_recommendations(user_id, limit)
    
    recommendations = []
    
    # 基于用户兴趣推荐
    if user_data:
        interest_recs = recommend_by_interests(user_data, papers, limit // 2)
        recommendations.extend(interest_recs)
        
        # 基于阅读历史推荐
        history_recs = recommend_by_reading_history(user_data, papers, limit // 3)
        recommendations.extend(history_recs)
        
        # 基于关注作者推荐
        author_recs = recommend_by_followed_authors(user_data, papers, limit // 4)
        recommendations.extend(author_recs)
    
    # 热门论文推荐
    trending_recs = recommend_trending_papers(papers, limit // 4)
    recommendations.extend(trending_recs)
    
    # 去重和排序
    seen_papers = set()
    unique_recs = []
    for rec in recommendations:
        if rec["paper_id"] not in seen_papers:
            seen_papers.add(rec["paper_id"])
            unique_recs.append(rec)
    
    # 按推荐分数排序
    unique_recs.sort(key=lambda x: x["score"], reverse=True)
    
    return unique_recs[:limit]

def recommend_by_interests(user_data: Dict[str, Any], papers: List[Dict[str, Any]], 
                          limit: int = 5) -> List[Dict[str, Any]]:
    """
    基于用户研究兴趣推荐论文
    """
    user_interests = user_data.get("research_interests", [])
    if not user_interests:
        return []
    
    recommendations = []
    
    for paper in papers:
        score = 0.0
        matching_keywords = []
        
        # 检查关键词匹配
        paper_keywords = paper.get("keywords", [])
        paper_field = paper.get("research_field", "")
        
        for interest in user_interests:
            interest_lower = interest.lower()
            
            # 检查研究领域匹配
            if interest_lower in paper_field.lower():
                score += 0.8
                matching_keywords.append(interest)
            
            # 检查关键词匹配
            for keyword in paper_keywords:
                if interest_lower in keyword.lower():
                    score += 0.6
                    matching_keywords.append(keyword)
        
        # 加入时效性因素
        current_year = datetime.now().year
        years_old = current_year - paper.get("year", 2020)
        recency_bonus = max(0, 0.3 - years_old * 0.1)
        score += recency_bonus
        
        # 加入影响力因素
        citation_count = paper.get("citation_count", 0)
        impact_bonus = min(0.5, math.log(citation_count + 1) * 0.1)
        score += impact_bonus
        
        if score > 0:
            reason = f"匹配你的研究兴趣：{', '.join(matching_keywords[:3])}"
            recommendations.append({
                "paper_id": paper["id"],
                "score": round(score, 3),
                "reason": reason,
                "type": "interest_based"
            })
    
    return sorted(recommendations, key=lambda x: x["score"], reverse=True)[:limit]

def recommend_by_reading_history(user_data: Dict[str, Any], papers: List[Dict[str, Any]], 
                                limit: int = 3) -> List[Dict[str, Any]]:
    """
    基于用户阅读历史推荐相似论文
    """
    reading_history = user_data.get("reading_history", [])
    if not reading_history:
        return []
    
    # 获取历史阅读论文的特征
    historical_keywords = []
    historical_authors = []
    historical_fields = []
    
    for paper in papers:
        if paper["id"] in reading_history:
            historical_keywords.extend(paper.get("keywords", []))
            historical_authors.extend(paper.get("authors", []))
            historical_fields.append(paper.get("research_field", ""))
    
    # 统计频次
    keyword_freq = Counter(historical_keywords)
    author_freq = Counter(historical_authors)
    field_freq = Counter(historical_fields)
    
    recommendations = []
    
    for paper in papers:
        if paper["id"] in reading_history:
            continue  # 跳过已读论文
        
        score = 0.0
        reasons = []
        
        # 基于关键词相似性
        common_keywords = set(paper.get("keywords", [])) & set(keyword_freq.keys())
        if common_keywords:
            keyword_score = sum(keyword_freq[kw] for kw in common_keywords) * 0.3
            score += keyword_score
            reasons.append(f"与你的阅读偏好相关")
        
        # 基于作者相似性
        common_authors = set(paper.get("authors", [])) & set(author_freq.keys())
        if common_authors:
            author_score = len(common_authors) * 0.4
            score += author_score
            reasons.append(f"你曾阅读过相关作者的论文")
        
        # 基于研究领域相似性
        paper_field = paper.get("research_field", "")
        if paper_field in field_freq:
            field_score = field_freq[paper_field] * 0.2
            score += field_score
            reasons.append(f"属于你关注的研究领域")
        
        if score > 0:
            reason = "；".join(reasons)
            recommendations.append({
                "paper_id": paper["id"],
                "score": round(score, 3),
                "reason": reason,
                "type": "history_based"
            })
    
    return sorted(recommendations, key=lambda x: x["score"], reverse=True)[:limit]

def recommend_by_followed_authors(user_data: Dict[str, Any], papers: List[Dict[str, Any]], 
                                 limit: int = 3) -> List[Dict[str, Any]]:
    """
    基于用户关注的作者推荐论文
    """
    followed_authors = user_data.get("followed_authors", [])
    if not followed_authors:
        return []
    
    recommendations = []
    
    for paper in papers:
        paper_authors = paper.get("authors", [])
        
        # 检查是否有关注的作者
        common_authors = set(paper_authors) & set(followed_authors)
        if common_authors:
            # 基础分数
            score = len(common_authors) * 0.8
            
            # 论文新颖性加分
            current_year = datetime.now().year
            years_old = current_year - paper.get("year", 2020)
            if years_old <= 1:
                score += 0.5
            
            # 影响力加分
            citation_count = paper.get("citation_count", 0)
            if citation_count > 50:
                score += 0.3
            
            reason = f"来自你关注的作者的最新研究"
            recommendations.append({
                "paper_id": paper["id"],
                "score": round(score, 3),
                "reason": reason,
                "type": "author_based"
            })
    
    return sorted(recommendations, key=lambda x: x["score"], reverse=True)[:limit]

def recommend_trending_papers(papers: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """
    推荐热门/趋势论文
    """
    recommendations = []
    
    for paper in papers:
        # 计算热门度分数
        citation_count = paper.get("citation_count", 0)
        download_count = paper.get("download_count", 0)
        year = paper.get("year", 2020)
        
        # 综合热门度计算
        citation_score = math.log(citation_count + 1)
        download_score = math.log(download_count + 1) * 0.5
        recency_score = max(0, 2024 - year)  # 越新越好
        
        trending_score = citation_score + download_score - recency_score * 0.2
        
        if trending_score > 3.0:  # 热门阈值
            recommendations.append({
                "paper_id": paper["id"],
                "score": round(trending_score, 3),
                "reason": "当前热门论文",
                "type": "trending"
            })
    
    return sorted(recommendations, key=lambda x: x["score"], reverse=True)[:limit]

def rerank_search_results(user_id: str, results: List[Dict[str, Any]], 
                         user_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    基于用户偏好重新排序搜索结果
    
    Args:
        user_id: 用户ID
        results: 原始搜索结果
        user_data: 用户数据
    
    Returns:
        重新排序后的搜索结果
    """
    if not user_data:
        return results
    
    user_interests = user_data.get("research_interests", [])
    reading_history = user_data.get("reading_history", [])
    followed_authors = user_data.get("followed_authors", [])
    
    # 为每个结果计算个性化分数
    for result in results:
        personalization_score = 0.0
        
        # 基于研究兴趣调整
        paper_keywords = result.get("keywords", [])
        paper_field = result.get("research_field", "")
        for interest in user_interests:
            if interest.lower() in paper_field.lower():
                personalization_score += 0.3
            for keyword in paper_keywords:
                if interest.lower() in keyword.lower():
                    personalization_score += 0.2
        
        # 基于关注作者调整
        paper_authors = result.get("authors", [])
        author_match = len(set(paper_authors) & set(followed_authors))
        personalization_score += author_match * 0.4
        
        # 基于阅读历史调整（避免重复）
        if result["id"] in reading_history:
            personalization_score -= 0.5  # 降低已读论文的排序
        
        # 更新分数（原始相关性分数 + 个性化分数）
        original_score = result.get("relevance_score", 1.0)
        result["final_score"] = original_score + personalization_score
    
    # 按最终分数重新排序
    return sorted(results, key=lambda x: x.get("final_score", 0), reverse=True)

def generate_mock_recommendations(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    生成模拟推荐数据（用于演示）
    """
    mock_papers = [
        "paper_001", "paper_002", "paper_003", "paper_004", "paper_005"
    ]
    
    recommendations = []
    reasons = [
        "基于你对深度学习的兴趣",
        "你关注的作者发表的新论文",
        "与你的阅读历史相关",
        "当前热门研究领域",
        "推荐系统算法建议"
    ]
    
    for i in range(min(limit, len(mock_papers))):
        recommendations.append({
            "paper_id": mock_papers[i],
            "score": round(random.uniform(0.6, 0.95), 3),
            "reason": reasons[i % len(reasons)],
            "type": "mock",
            "created_at": datetime.now().isoformat()
        })
    
    return recommendations

def get_recommendation_explanation(recommendation: Dict[str, Any]) -> str:
    """
    获取推荐理由的详细解释
    """
    rec_type = recommendation.get("type", "unknown")
    score = recommendation.get("score", 0.0)
    
    explanations = {
        "interest_based": "基于你的研究兴趣匹配",
        "history_based": "基于你的阅读历史相似性分析", 
        "author_based": "来自你关注的作者",
        "trending": "当前学术界热门研究",
        "collaborative": "与你相似的用户也在关注",
        "mock": "智能推荐算法建议"
    }
    
    base_explanation = explanations.get(rec_type, "基于综合算法推荐")
    
    if score >= 0.8:
        confidence = "高度推荐"
    elif score >= 0.6:
        confidence = "推荐"
    else:
        confidence = "可能感兴趣"
    
    return f"{base_explanation}（{confidence}）"

def update_user_preferences(user_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    基于用户交互更新偏好模型
    
    Args:
        user_id: 用户ID
        interaction_data: 交互数据（点击、收藏、阅读时长等）
    
    Returns:
        更新后的偏好模型
    """
    # 这里实现偏好学习逻辑
    # 在实际应用中，这里会更新用户的兴趣向量、权重等
    
    interaction_type = interaction_data.get("type", "view")
    paper_id = interaction_data.get("paper_id")
    timestamp = interaction_data.get("timestamp", datetime.now().isoformat())
    
    # 模拟偏好更新
    updated_preferences = {
        "user_id": user_id,
        "last_update": timestamp,
        "interaction_count": interaction_data.get("interaction_count", 1),
        "preference_strength": calculate_preference_strength(interaction_type)
    }
    
    return updated_preferences

def calculate_preference_strength(interaction_type: str) -> float:
    """
    根据交互类型计算偏好强度
    """
    strength_mapping = {
        "view": 0.1,
        "download": 0.3,
        "bookmark": 0.5,
        "share": 0.4,
        "cite": 0.8,
        "full_read": 0.6
    }
    
    return strength_mapping.get(interaction_type, 0.1)

