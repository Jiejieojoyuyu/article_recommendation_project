"""
数据库管理模块 - 自动检测和创建缺失的表和索引
"""
import sqlite3
import aiosqlite
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器 - 负责数据库的初始化、升级和维护"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.required_tables = {
            'users': self._get_users_table_schema(),
            'user_folders': self._get_user_folders_table_schema(),
            'folder_papers': self._get_folder_papers_table_schema(),
            'user_follows': self._get_user_follows_table_schema(),
            'user_search_history': self._get_user_search_history_table_schema(),
            'user_bookmarks': self._get_user_bookmarks_table_schema(),
            'user_reading_history': self._get_user_reading_history_table_schema()
        }
        self.required_indexes = self._get_required_indexes()
    
    def _get_users_table_schema(self) -> str:
        """获取users表的创建语句"""
        return """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            affiliation TEXT,
            research_interests TEXT,
            created_at TEXT NOT NULL,
            last_login TEXT,
            updated_at TEXT
        )
        """
    
    def _get_user_folders_table_schema(self) -> str:
        """获取user_folders表的创建语句"""
        return """
        CREATE TABLE IF NOT EXISTS user_folders (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    
    def _get_folder_papers_table_schema(self) -> str:
        """获取folder_papers表的创建语句"""
        return """
        CREATE TABLE IF NOT EXISTS folder_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id TEXT NOT NULL,
            paper_id TEXT NOT NULL,
            added_at TEXT NOT NULL,
            FOREIGN KEY (folder_id) REFERENCES user_folders (id)
        )
        """
    
    def _get_user_follows_table_schema(self) -> str:
        """获取user_follows表的创建语句"""
        return """
        CREATE TABLE IF NOT EXISTS user_follows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            author_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, author_id)
        )
        """
    
    def _get_user_search_history_table_schema(self) -> str:
        """获取user_search_history表的创建语句"""
        return """
        CREATE TABLE IF NOT EXISTS user_search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            query TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    
    def _get_user_bookmarks_table_schema(self) -> str:
        """获取user_bookmarks表的创建语句"""
        return """
        CREATE TABLE IF NOT EXISTS user_bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            paper_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, paper_id)
        )
        """
    
    def _get_user_reading_history_table_schema(self) -> str:
        """获取user_reading_history表的创建语句"""
        return """
        CREATE TABLE IF NOT EXISTS user_reading_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            paper_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    
    def _get_required_indexes(self) -> List[Dict[str, str]]:
        """获取必需的索引列表"""
        return [
            {
                'name': 'idx_user_folders_user_id',
                'table': 'user_folders',
                'columns': 'user_id'
            },
            {
                'name': 'idx_folder_papers_folder_id',
                'table': 'folder_papers',
                'columns': 'folder_id'
            },
            {
                'name': 'idx_user_follows_user_id',
                'table': 'user_follows',
                'columns': 'user_id'
            },
            {
                'name': 'idx_user_search_history_user_id',
                'table': 'user_search_history',
                'columns': 'user_id'
            },
            {
                'name': 'idx_user_bookmarks_user_id',
                'table': 'user_bookmarks',
                'columns': 'user_id'
            },
            {
                'name': 'idx_user_reading_history_user_id',
                'table': 'user_reading_history',
                'columns': 'user_id'
            }
        ]
    
    async def initialize_database(self) -> bool:
        """初始化数据库 - 创建缺失的表和索引"""
        try:
            logger.info(f"开始初始化数据库: {self.db_path}")
            
            # 检查数据库文件是否存在
            if not os.path.exists(self.db_path):
                logger.error(f"数据库文件不存在: {self.db_path}")
                return False
            
            # 获取现有表列表
            existing_tables = await self._get_existing_tables()
            logger.info(f"现有表: {existing_tables}")
            
            # 创建缺失的表
            await self._create_missing_tables(existing_tables)
            
            # 获取现有索引列表
            existing_indexes = await self._get_existing_indexes()
            logger.info(f"现有索引: {existing_indexes}")
            
            # 创建缺失的索引
            await self._create_missing_indexes(existing_indexes)
            
            # 插入默认用户数据
            await self._insert_default_data()
            
            logger.info("数据库初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            return False
    
    async def _get_existing_tables(self) -> List[str]:
        """获取数据库中现有的表列表"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = await cursor.fetchall()
            return [table[0] for table in tables]
    
    async def _get_existing_indexes(self) -> List[str]:
        """获取数据库中现有的索引列表"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = await cursor.fetchall()
            return [index[0] for index in indexes]
    
    async def _create_missing_tables(self, existing_tables: List[str]):
        """创建缺失的表"""
        async with aiosqlite.connect(self.db_path) as db:
            for table_name, schema in self.required_tables.items():
                if table_name not in existing_tables:
                    logger.info(f"创建表: {table_name}")
                    await db.execute(schema)
                    await db.commit()
                else:
                    logger.info(f"表已存在: {table_name}")
    
    async def _create_missing_indexes(self, existing_indexes: List[str]):
        """创建缺失的索引"""
        async with aiosqlite.connect(self.db_path) as db:
            for index_info in self.required_indexes:
                if index_info['name'] not in existing_indexes:
                    logger.info(f"创建索引: {index_info['name']}")
                    create_index_sql = f"CREATE INDEX {index_info['name']} ON {index_info['table']}({index_info['columns']})"
                    await db.execute(create_index_sql)
                    await db.commit()
                else:
                    logger.info(f"索引已存在: {index_info['name']}")
    
    async def _insert_default_data(self):
        """插入默认数据"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 检查是否已有用户数据
                cursor = await db.execute("SELECT COUNT(*) FROM users")
                count = await cursor.fetchone()
                
                if count[0] == 0:
                    logger.info("插入默认用户数据")
                    # 插入测试用户
                    test_user_sql = """
                    INSERT INTO users (id, username, email, password_hash, full_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """
                    await db.execute(test_user_sql, (
                        "test_user_001",
                        "student_zhang",
                        "student@example.com",
                        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8QqHh2",  # password
                        "张同学",
                        datetime.now().isoformat()
                    ))
                    await db.commit()
                    logger.info("默认用户数据插入完成")
                else:
                    logger.info("用户数据已存在，跳过默认数据插入")
                    
        except Exception as e:
            logger.warning(f"插入默认数据失败: {str(e)}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取表信息
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # 获取索引信息
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = [row[0] for row in cursor.fetchall()]
                
                # 获取数据库大小
                file_size = os.path.getsize(self.db_path)
                
                return {
                    "database_path": self.db_path,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "tables": tables,
                    "indexes": indexes,
                    "required_tables": list(self.required_tables.keys()),
                    "required_indexes": [idx['name'] for idx in self.required_indexes]
                }
                
        except Exception as e:
            logger.error(f"获取数据库信息失败: {str(e)}")
            return {"error": str(e)}
    
    async def check_database_health(self) -> Dict[str, Any]:
        """检查数据库健康状态"""
        try:
            health_status = {
                "status": "healthy",
                "issues": [],
                "recommendations": []
            }
            
            # 检查必需的表
            existing_tables = await self._get_existing_tables()
            missing_tables = []
            for table in self.required_tables.keys():
                if table not in existing_tables:
                    missing_tables.append(table)
            
            if missing_tables:
                health_status["status"] = "unhealthy"
                health_status["issues"].append(f"缺失必需的表: {missing_tables}")
                health_status["recommendations"].append("运行数据库初始化以创建缺失的表")
            
            # 检查必需的索引
            existing_indexes = await self._get_existing_indexes()
            missing_indexes = []
            for index_info in self.required_indexes:
                if index_info['name'] not in existing_indexes:
                    missing_indexes.append(index_info['name'])
            
            if missing_indexes:
                health_status["status"] = "unhealthy"
                health_status["issues"].append(f"缺失必需的索引: {missing_indexes}")
                health_status["recommendations"].append("运行数据库初始化以创建缺失的索引")
            
            # 检查数据库连接
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("SELECT 1")
                health_status["connection"] = "ok"
            except Exception as e:
                health_status["status"] = "unhealthy"
                health_status["connection"] = "failed"
                health_status["issues"].append(f"数据库连接失败: {str(e)}")
            
            return health_status
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "issues": ["无法检查数据库健康状态"]
            }
