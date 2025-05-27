from sqlalchemy.orm import Session
from typing import Type, Any

def get_all_files(db: Session, model_class: Type[Any]):
    return db.query(model_class).all()

def create_file(db: Session, model_class: Type[Any], name: str, thumbnail: str):
    db_file = model_class(name=name, thumbnail=thumbnail)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def delete_file(db: Session, model_class: Type[Any], id: int):
    db_file = db.query(model_class).get(id)
    print(db_file)
    try:
        db.delete(db_file)
        db.commit()
        print("✅ 删除成功")
    except Exception as e:
        db.rollback()
        print("❌ 删除失败:", str(e))
    return db_file

def delete_all(db: Session, model_class: Type[Any]):
    try:
        row_count = db.query(model_class).delete()
        db.commit()
        print(f"✅ 成功删除 {row_count} 条记录")
        return {"success": True, "deleted_count": row_count}
    except Exception as e:
        db.rollback()
        print("❌ 删除失败:", str(e))
        return {"success": False, "error": str(e)}