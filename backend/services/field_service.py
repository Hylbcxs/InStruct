from sqlalchemy.orm import Session
from typing import Type, Any

# 更新抽取字段
def update_extracted_default_field(db: Session, model_class: Type[Any], id: int, extracted_data: dict):
    db_file = db.query(model_class).get(id)
    if db_file:
        db_file.ExtractedDefaultField = extracted_data  # 更新字段
        db.commit()
        db.refresh(db_file)
    return db_file

# 查询出默认抽取字段
def get_extracted_default_field(db: Session, model_class: Type[Any], id: int):
    db_file = db.query(model_class).get(id)
    if db_file:
        return db_file.ExtractedDefaultField
    return None

# 更新自定义抽取字段
def update_extracted_custom_field(db: Session, model_class: Type[Any], id: int, extracted_data: dict):
    db_file = db.query(model_class).get(id)
    if db_file:
        db_file.ExtractedCustomField = extracted_data  # 更新字段
        db.commit()
        db.refresh(db_file)
    return db_file

# 查询自定义抽取字段
def get_extracted_custom_field(db: Session, model_class: Type[Any], id: int):
    db_file = db.query(model_class).get(id)
    if db_file:
        return db_file.ExtractedCustomField
    return None

# 开启loading字段
def update_open_loading(db: Session, model_class: Type[Any],id: int):
    db_file = db.query(model_class).get(id)
    if db_file:
        db_file.loading_auto = True
        db_file.loadingText = "正在抽取字段..."
        db.commit()
        db.refresh(db_file)
    return db_file

# 关闭loading字段
def update_close_loading(db: Session, model_class: Type[Any],id: int):
    db_file = db.query(model_class).get(id)
    if db_file:
        db_file.loading_auto = False
        db_file.loadingText = ""
        db.commit()
        db.refresh(db_file)
    return db_file