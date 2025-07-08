from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from typing_extensions import Annotated
from typing import List

from database.database import get_db

# Service functions（假设它们支持传入 model_class）
from services.field_service import (
    update_extracted_default_field,
    get_extracted_default_field,
    update_extracted_custom_field,
    get_extracted_custom_field,
    update_open_loading,
    update_close_loading,
    update_standard_field,
    get_standard_field
)

def create_field_router(model_class, url_prefix: str = "/fields"):
    router = APIRouter(prefix=url_prefix)

    # 保存默认字段
    @router.post("/save-extracted")
    def save_extracted(
        file_id: Annotated[int, Body(...)],
        extracted_data: Annotated[List[dict], Body(...)],
        db: Session = Depends(get_db)
    ):
        updated_file = update_extracted_default_field(db, model_class, file_id, extracted_data)
        if not updated_file:
            raise HTTPException(status_code=404, detail="文件未找到")
        return {"message": "提取字段保存成功", "data": updated_file}

    # 查询默认字段
    @router.get("/extracted-field/{file_id}")
    def read_extracted_field(file_id: int, db: Session = Depends(get_db)):
        extracted_data = get_extracted_default_field(db, model_class, file_id)
        standard_data = get_standard_field(db, model_class, file_id)
        if standard_data:
            extracted_data = standard_data
        if not extracted_data:
            return {"file_id": file_id, "extracted_data": ''}
        return {"file_id": file_id, "extracted_data": extracted_data}

    # 保存自定义字段
    @router.post("/save-custom-extracted")
    def save_custom_extracted(
        file_id: Annotated[int, Body(...)],
        extracted_data: Annotated[List[dict], Body(...)],
        db: Session = Depends(get_db)
    ):
        updated_file = update_extracted_custom_field(db, model_class, file_id, extracted_data)
        if not updated_file:
            raise HTTPException(status_code=404, detail="文件未找到")
        return {"message": "自定义字段保存成功", "data": updated_file}

    # 查询自定义字段
    @router.get("/extracted-custom-field/{file_id}")
    def read_extracted_custom_field(file_id: int, db: Session = Depends(get_db)):
        extracted_data = get_extracted_custom_field(db, model_class, file_id)
        if not extracted_data:
            return {"file_id": file_id, "extracted_data": ''}
        return {"file_id": file_id, "extracted_data": extracted_data}

    @router.post("/save-standard-field")
    def save_standard_field(
        file_id: Annotated[int, Body(...)],
        standard_data: Annotated[List[dict], Body(...)],
        db: Session = Depends(get_db)
    ):
        updated_file = update_standard_field(db, model_class, file_id, standard_data)
        if not updated_file:
            raise HTTPException(status_code=404, detail="文件未找到")
        return {"message": "标准字段保存成功", "data": updated_file}

    # 开启 loading
    @router.post("/open-loading")
    def open_loading(file_id: Annotated[int, Body(embed=True)], db: Session = Depends(get_db)):
        updated_file = update_open_loading(db, model_class, file_id)
        if not updated_file:
            raise HTTPException(status_code=404, detail="文件未找到")
        return {"message": "success", "data": updated_file}

    # 关闭 loading
    @router.post("/close-loading")
    def close_loading(file_id: Annotated[int, Body(embed=True)], db: Session = Depends(get_db)):
        updated_file = update_close_loading(db, model_class, file_id)
        if not updated_file:
            raise HTTPException(status_code=404, detail="文件未找到")
        return {"message": "success", "data": updated_file}

    return router