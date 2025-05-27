from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FileBaseMixin:
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    thumbnail = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # 可以共用的字段
    ExtractedDefaultField = Column(JSON, default=[])
    ExtractedCustomField = Column(JSON, default=[])
    loadingText = Column(String(255))
    loading_auto = Column(Boolean, default=False)
    loading_cutom = Column(Boolean, default=False)