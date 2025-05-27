from database.database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from models.fileBaseMixin import FileBaseMixin

# class InvoiceModel(Base):
#     __tablename__ = 'invoice'
    # id = Column(Integer, primary_key=True)
    # name = Column(String(255), nullable=False)
    # thumbnail = Column(String(255), nullable=False)
    # created_at = Column(DateTime, default=func.now())
    # # extractedDefaultFields = relationship("ExtractedField", back_populates="file")
    # ExtractedDefaultField = Column(JSON, default=[])
    # ExtractedCustomField = Column(JSON, default=[])
    # loadingText = Column(String(255))
    # loading_auto = Column(Boolean, default=False)
    # loading_cutom = Column(Boolean, default=False)
# 发票
class InvoiceModel(Base, FileBaseMixin):
    __tablename__ = 'invoice'
# 报关单
class DeclarationModel(Base, FileBaseMixin):
    __tablename__ = 'declaration'
# 合同
class ContractModel(Base, FileBaseMixin):
    __tablename__ = 'contract'
# 提单
class LandingModel(Base, FileBaseMixin):
    __tablename__ = 'landing'




