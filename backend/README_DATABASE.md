# 数据库管理功能说明

## 概述

本项目现在具备了自动数据库管理功能，可以自动检测并创建缺失的表和索引，解决了接入新数据库时缺少用户相关表的问题。

## 🆕 新增功能

### 1. 自动数据库初始化
- **自动检测缺失的表和索引**
- **自动创建用户相关的表结构**
- **自动插入默认测试数据**
- **支持多种数据库文件**

### 2. 数据库配置管理
- **支持多个数据库文件切换**
- **智能推荐最佳数据库**
- **配置文件持久化**
- **环境变量支持**

### 3. 数据库健康监控
- **实时健康状态检查**
- **问题诊断和建议**
- **连接状态监控**

## 📁 文件结构

```
backend/app/db/
├── database.py              # 主数据库操作模块（已增强）
├── database_manager.py      # 数据库管理器（新增）
├── config.py                # 数据库配置管理（新增）
└── __init__.py
```

## 🚀 使用方法

### 1. 自动初始化（推荐）

程序会在首次连接数据库时自动检测并初始化缺失的表和索引，无需手动操作。

### 2. 手动初始化

如果需要手动初始化数据库，可以使用以下API：

```bash
# 检查数据库健康状态
GET /api/database/health

# 获取数据库信息
GET /api/database/info

# 手动初始化数据库
POST /api/database/initialize

# 获取数据库配置
GET /api/database/config

# 切换数据库
POST /api/database/switch/{db_name}
```

### 3. 测试脚本

运行测试脚本来验证功能：

```bash
cd backend
python test_database_init.py
```

## 🔧 配置说明

### 环境变量

```bash
# 设置要使用的数据库文件
export DATABASE_FILE=openalex_v3
```

### 配置文件

程序会在项目根目录创建 `.database_config` 文件来保存数据库选择。

### 可用数据库

| 数据库名称 | 文件 | 大小 | 特点 |
|-----------|------|------|------|
| openalex_v1 | openalex_v1.db | 1.2GB | 包含完整的用户表 |
| openalex_v3 | openalex_v3.db | 12GB | 爬虫生成，需要自动初始化 |

## 📊 自动创建的表

程序会自动创建以下表：

### 1. users - 用户表
```sql
CREATE TABLE users (
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
);
```

### 2. user_folders - 用户收藏夹
```sql
CREATE TABLE user_folders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### 3. folder_papers - 收藏夹论文
```sql
CREATE TABLE folder_papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id TEXT NOT NULL,
    paper_id TEXT NOT NULL,
    added_at TEXT NOT NULL,
    FOREIGN KEY (folder_id) REFERENCES user_folders (id)
);
```

### 4. user_follows - 用户关注
```sql
CREATE TABLE user_follows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, author_id)
);
```

### 5. user_search_history - 搜索历史
```sql
CREATE TABLE user_search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## 🔍 自动创建的索引

程序会自动创建以下索引：

- `idx_user_folders_user_id` - 用户收藏夹用户ID索引
- `idx_folder_papers_folder_id` - 收藏夹论文文件夹ID索引
- `idx_user_follows_user_id` - 用户关注用户ID索引
- `idx_user_search_history_user_id` - 搜索历史用户ID索引

## 🧪 测试数据

程序会自动插入一个测试用户：

- **用户名**: `student_zhang`
- **密码**: `password`
- **邮箱**: `student@example.com`

## ⚠️ 注意事项

1. **首次启动**: 程序首次连接新数据库时会自动初始化，可能需要几秒钟
2. **权限要求**: 确保程序对数据库文件有读写权限
3. **备份建议**: 在切换数据库前建议备份重要数据
4. **性能影响**: 初始化过程会短暂影响数据库性能

## 🐛 故障排除

### 常见问题

1. **初始化失败**
   - 检查数据库文件权限
   - 确保有足够的磁盘空间
   - 查看日志文件

2. **表创建失败**
   - 检查数据库是否被其他程序锁定
   - 验证数据库文件完整性

3. **连接错误**
   - 确认数据库文件路径正确
   - 检查文件是否存在

### 日志查看

程序会输出详细的初始化日志，包括：
- 表创建状态
- 索引创建状态
- 错误信息
- 成功确认

## 🔮 未来计划

- [ ] 支持更多数据库类型（PostgreSQL, MySQL）
- [ ] 数据库迁移功能
- [ ] 自动备份和恢复
- [ ] 性能监控和优化建议
- [ ] 图形化管理界面

## 📞 技术支持

如果遇到问题，请：

1. 查看程序日志输出
2. 运行测试脚本 `test_database_init.py`
3. 检查数据库健康状态 API
4. 提交 Issue 并提供详细错误信息

---

**数据库管理功能** - 让数据库接入更简单、更智能！ 🎉

