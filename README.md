# 学术论文推荐系统

一个功能丰富、界面精美的高级学术论文推荐Web应用系统。采用前后端分离架构，集成了智能搜索、深度分析、个性化推荐等先进功能。

## 🚀 项目特色

### 核心功能
- **智能搜索引擎**：混合搜索、语义搜索、精确搜索，支持动态筛选和多维度排序
- **深度论文分析**：真值算法评估、引用网络分析、相似论文发现
- **学者全景画像**：学术轨迹分析、合作网络可视化、研究焦点变迁
- **知识图谱浏览**：交互式引用关系图、合作网络图谱
- **AI学术助手**：论文总结、跨文献对比、研究趋势分析、研究思路生成
- **个人工作台**：多层级收藏夹、关注列表、阅读历史、智能推荐

### 技术亮点
- **后端**：FastAPI + Python，高性能异步API
- **前端**：Vue 3 + TypeScript + Tailwind CSS，现代化响应式界面
- **算法模块**：真值计算算法、个性化推荐算法
- **数据可视化**：ECharts图表、D3.js/G6知识图谱
- **UI/UX**：暗色/亮色模式切换、平滑动画、微交互设计

## 📁 项目结构

```
academic_project/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由模块
│   │   │   ├── auth.py     # 用户认证
│   │   │   ├── search.py   # 搜索功能
│   │   │   ├── papers.py   # 论文管理
│   │   │   ├── authors.py  # 学者管理
│   │   │   ├── workspace.py # 工作台
│   │   │   └── ai_assistant.py # AI助手
│   │   ├── algorithms/     # 算法模块
│   │   │   ├── truth_value.py  # 真值算法
│   │   │   └── recommender.py  # 推荐算法
│   │   ├── core/           # 核心模块
│   │   │   └── security.py # 安全认证
│   │   ├── db/             # 数据层
│   │   │   └── mock_db.py  # 模拟数据库
│   │   ├── models/         # 数据模型
│   │   │   ├── user.py     # 用户模型
│   │   │   └── paper.py    # 论文模型
│   │   └── main.py         # 应用入口
│   └── requirements.txt    # 依赖列表
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # 组件库
│   │   ├── views/          # 页面视图
│   │   ├── stores/         # 状态管理
│   │   ├── services/       # API服务
│   │   ├── router/         # 路由配置
│   │   └── assets/         # 静态资源
│   ├── package.json        # 项目配置
│   └── tailwind.config.js  # 样式配置
├── crawler/                # 数据爬虫
│   └── openalex_crawler.py # OpenAlex爬虫
└── README.md              # 项目文档
```

## 🛠️ 技术栈

### 后端技术
- **FastAPI**: 现代高性能Python Web框架
- **Pydantic**: 数据验证和序列化
- **PassLib**: 密码加密处理
- **Python-JOSE**: JWT令牌管理
- **Uvicorn**: ASGI服务器

### 前端技术
- **Vue 3**: 渐进式JavaScript框架
- **TypeScript**: 类型安全的JavaScript
- **Tailwind CSS**: 实用优先的CSS框架
- **Pinia**: Vue状态管理
- **Vue Router**: 单页应用路由
- **Axios**: HTTP客户端
- **ECharts**: 数据可视化图表
- **D3.js/G6**: 知识图谱可视化

### 数据与算法
- **OpenAlex API**: 学术数据源
- **模拟数据库**: 完整的测试数据集
- **真值算法**: 多维度论文质量评估
- **推荐算法**: 个性化内容推荐

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- npm/yarn

### 安装与运行

#### 1. 设置后端环境

```powershell
# 创建虚拟环境
python -m venv article_recommend

# 激活虚拟环境 (Windows PowerShell)
./article_recommend/Scripts/Activate.ps1

# 安装后端依赖
pip install -r ./backend/requirements.txt
```

#### 2. 安装前端依赖

```powershell
cd frontend
npm install
cd ..
```

#### 3. 启动服务

**启动后端服务：**
```powershell
# 在新的PowerShell窗口中运行
cd backend/app
uvicorn main:app --reload
```

**启动前端开发服务器：**
```powershell
# 在另一个PowerShell窗口中运行
cd frontend
npm run dev
```

### 访问应用

- **前端应用**: http://localhost:5173
- **后端API**: http://127.0.0.1:8000
- **API文档**: http://127.0.0.1:8000/docs
- **ReDoc文档**: http://127.0.0.1:8000/redoc

## 📚 功能演示

### 1. 用户系统
- 注册新账户
- 用户登录/登出
- 个人资料管理
- 密码修改

### 2. 智能搜索
- 混合搜索：同时匹配标题、作者、关键词
- 语义搜索：支持长句和段落查询
- 动态筛选：年份、期刊、研究领域、引用数
- 多种排序：相关度、时间、引用数、真值分数

### 3. 论文分析
- 详细的论文信息展示
- 真值分数计算与解释
- 参考文献和被引文献列表
- 相似论文推荐
- 引用关系网络图

### 4. 学者分析
- 学者基本信息和统计数据
- 学术生涯轨迹可视化
- 研究焦点变迁分析
- 合作网络图谱
- 代表作品列表

### 5. AI助手功能
- 论文一句话总结
- 多篇论文对比分析
- 研究领域趋势分析
- 论文详细解读
- 相关阅读推荐
- 研究思路生成

### 6. 个人工作台
- 多层级收藏夹管理
- 关注学者列表
- 阅读历史记录
- 个性化推荐列表
- 统计信息概览

## 🔧 配置说明

### 后端配置
- API基础URL: `http://127.0.0.1:8000/api`
- JWT密钥: 生产环境请修改`backend/app/core/security.py`中的密钥
- CORS设置: 已配置允许前端开发服务器访问

### 前端配置
- 开发服务器: `http://localhost:5173`
- API代理: 自动代理`/api`请求到后端
- 暗色模式: 支持系统偏好和手动切换

## 📊 数据说明

### 模拟数据库
项目包含完整的模拟数据，包括：
- 5篇示例论文，涵盖计算机科学各领域
- 3位示例学者，包含详细的学术信息
- 完整的引用关系网络
- 用户收藏、关注等交互数据

### 数据扩展
- 可使用`crawler/openalex_crawler.py`从OpenAlex API获取真实数据
- 支持自定义数据导入和扩展

## 🎨 界面特色

- **现代设计**: 简洁美观的Material Design风格
- **响应式布局**: 完美适配桌面端和移动端
- **暗色模式**: 护眼的深色主题
- **平滑动画**: 丰富的过渡效果和微交互
- **无障碍支持**: 键盘导航和屏幕阅读器友好

## 🔒 安全特性

- JWT令牌认证
- 密码哈希加密（BCrypt）
- API请求验证
- CORS跨域保护
- 输入数据验证

## 🧪 测试账户

系统预置了测试账户：
- 用户名: `student_zhang`
- 密码: `password`

也可以注册新账户进行测试。

## 📈 性能优化

- 前端代码分割和懒加载
- 图片和资源优化
- API响应缓存
- 虚拟化长列表
- 防抖搜索

## 🔮 未来规划

- [ ] 集成更多学术数据源
- [ ] 增强AI分析能力
- [ ] 实时协作功能
- [ ] 移动应用开发
- [ ] 高级可视化组件
- [ ] 学术社交网络

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证。详情请见[LICENSE](LICENSE)文件。

## 📞 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 邮件联系: contact@example.com

## 🙏 致谢

- OpenAlex API提供的开放学术数据
- Vue.js和FastAPI社区的优秀工具
- 所有贡献者的辛勤工作

---

**学术论文推荐系统** - 让学术研究更高效、更智能！

