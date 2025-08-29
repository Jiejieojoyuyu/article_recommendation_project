"""
数据库配置文件
允许用户选择不同的数据库文件
"""
import os
from pathlib import Path
from typing import Optional

class DatabaseConfig:
    """数据库配置管理类"""
    
    # 可用的数据库文件
    AVAILABLE_DATABASES = {
        "openalex_v1": {
            "path": "openalex_v1.db",
            "description": "OpenAlex V1 数据库 (1.2GB) - 包含用户表",
            "has_user_tables": True
        },
        "openalex_v3": {
            "path": "openalex_v3.db", 
            "description": "OpenAlex V3 数据库 (12GB) - 爬虫生成，需要自动初始化",
            "has_user_tables": False
        }
    }
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self._current_db = None
        self._load_config()
    
    def _load_config(self):
        """加载数据库配置"""
        # 检查环境变量
        env_db = os.getenv("DATABASE_FILE")
        if env_db:
            self._current_db = env_db
            return
        
        # 检查配置文件
        config_file = self.project_root / ".database_config"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._current_db = f.read().strip()
            except Exception:
                pass
        
        # 默认使用 openalex_v3
        if not self._current_db:
            self._current_db = "openalex_v1"
    
    def get_current_database(self) -> str:
        """获取当前选择的数据库名称"""
        return self._current_db
    
    def get_database_path(self, db_name: Optional[str] = None) -> Path:
        """获取数据库文件路径"""
        if db_name is None:
            db_name = self._current_db
        
        if db_name not in self.AVAILABLE_DATABASES:
            raise ValueError(f"未知的数据库: {db_name}")
        
        db_path = self.project_root / self.AVAILABLE_DATABASES[db_name]["path"]
        return db_path
    
    def get_database_info(self, db_name: Optional[str] = None) -> dict:
        """获取数据库信息"""
        if db_name is None:
            db_name = self._current_db
        
        if db_name not in self.AVAILABLE_DATABASES:
            return {"error": f"未知的数据库: {db_name}"}
        
        info = self.AVAILABLE_DATABASES[db_name].copy()
        db_path = self.get_database_path(db_name)
        
        # 检查文件是否存在
        if db_path.exists():
            info["exists"] = True
            info["file_size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 2)
        else:
            info["exists"] = False
            info["file_size_mb"] = 0
        
        info["full_path"] = str(db_path)
        return info
    
    def switch_database(self, db_name: str) -> bool:
        """切换数据库"""
        if db_name not in self.AVAILABLE_DATABASES:
            return False
        
        # 检查数据库文件是否存在
        db_path = self.get_database_path(db_name)
        if not db_path.exists():
            return False
        
        # 更新配置
        self._current_db = db_name
        
        # 保存到配置文件
        config_file = self.project_root / ".database_config"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(db_name)
            return True
        except Exception:
            return False
    
    def list_available_databases(self) -> dict:
        """列出所有可用的数据库"""
        result = {}
        for db_name, info in self.AVAILABLE_DATABASES.items():
            result[db_name] = self.get_database_info(db_name)
            result[db_name]["is_current"] = (db_name == self._current_db)
        
        return result
    
    def get_recommended_database(self) -> str:
        """获取推荐的数据库"""
        # 优先选择有用户表的数据库
        for db_name, info in self.AVAILABLE_DATABASES.items():
            if info["has_user_tables"]:
                db_path = self.get_database_path(db_name)
                if db_path.exists():
                    return db_name
        
        # 如果没有有用户表的数据库，选择第一个存在的
        for db_name, info in self.AVAILABLE_DATABASES.items():
            db_path = self.get_database_path(db_name)
            if db_path.exists():
                return db_name
        
        return "openalex_v3"  # 默认

# 全局配置实例
db_config = DatabaseConfig()

