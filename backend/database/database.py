from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
import json
from dotenv import load_dotenv
import os

load_dotenv()

# 配置
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# 带数据库的 URL（用于建表）
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"

# 不带数据库的 URL（用于创建数据库）
SQLALCHEMY_META_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/"

# 创建无数据库引擎（用于执行 CREATE DATABASE）
meta_engine = create_engine(SQLALCHEMY_META_URL)

engine = create_engine(SQLALCHEMY_DATABASE_URL, 
                       json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
                    )
SessionLocal = sessionmaker(autoflush=False, bind=engine)
Base = declarative_base()

def create_database():
    """创建数据库（如果不存在）"""
    with meta_engine.connect() as conn:
        conn.execute(text("COMMIT"))  # 确保没有事务挂起
        conn.execute(text(f"""
            CREATE DATABASE IF NOT EXISTS {DB_NAME} 
            CHARACTER SET utf8mb4 
            COLLATE utf8mb4_unicode_ci
        """))
        print(f"✅ 数据库 `{DB_NAME}` 已创建（如果不存在）")

def create_tables():
    """创建所有模型对应的表"""
    Base.metadata.create_all(bind=engine)
    print("✅ 所有表已创建（如果不存在）")

def init_db():
    """主初始化函数：先创建数据库，再创建表"""
    create_database()
    create_tables()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()