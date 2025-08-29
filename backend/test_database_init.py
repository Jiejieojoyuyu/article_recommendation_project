"""
测试数据库初始化功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_database_initialization():
    """测试数据库初始化"""
    try:
        print("🔍 测试数据库初始化功能...")
        
        # 导入数据库管理器
        from backend.app.db.database_manager import DatabaseManager
        from backend.app.db.config import db_config
        
        # 获取当前数据库配置
        current_db = db_config.get_current_database()
        db_path = db_config.get_database_path()
        
        print(f"📊 当前数据库: {current_db}")
        print(f"📁 数据库路径: {db_path}")
        
        # 检查数据库文件是否存在
        if not db_path.exists():
            print(f"❌ 数据库文件不存在: {db_path}")
            return False
        
        print(f"✅ 数据库文件存在，大小: {db_path.stat().st_size / (1024*1024):.2f} MB")
        
        # 创建数据库管理器
        db_manager = DatabaseManager(str(db_path))
        
        # 获取数据库信息
        db_info = db_manager.get_database_info()
        print(f"📋 数据库信息: {db_info}")
        
        # 检查数据库健康状态
        print("🏥 检查数据库健康状态...")
        health_status = await db_manager.check_database_health()
        print(f"健康状态: {health_status}")
        
        # 如果数据库不健康，尝试初始化
        if health_status.get("status") != "healthy":
            print("⚠️  数据库不健康，开始初始化...")
            success = await db_manager.initialize_database()
            if success:
                print("✅ 数据库初始化成功")
                
                # 再次检查健康状态
                health_status = await db_manager.check_database_health()
                print(f"初始化后健康状态: {health_status}")
            else:
                print("❌ 数据库初始化失败")
                return False
        else:
            print("✅ 数据库健康状态良好")
        
        # 测试数据库连接
        print("🔌 测试数据库连接...")
        try:
            from backend.app.db.database import db
            # 尝试获取一些数据
            papers = await db.get_papers(limit=5)
            print(f"✅ 成功获取 {len(papers)} 篇论文")
            
            # 测试用户管理
            from backend.app.db.database import user_manager
            users = await user_manager.get_users(limit=5)
            print(f"✅ 成功获取 {len(users)} 个用户")
            
        except Exception as e:
            print(f"❌ 数据库连接测试失败: {str(e)}")
            return False
        
        print("🎉 所有测试通过！数据库初始化功能正常工作。")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🚀 开始测试数据库初始化功能")
    print("=" * 50)
    
    success = await test_database_initialization()
    
    print("=" * 50)
    if success:
        print("🎯 测试结果: 成功")
        sys.exit(0)
    else:
        print("💥 测试结果: 失败")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
