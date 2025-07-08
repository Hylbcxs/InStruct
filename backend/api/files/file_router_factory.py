from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from services.file_service import create_file, delete_file, get_all_files, delete_all
from fastapi.responses import FileResponse
import os
import shutil

def create_file_router(model_class, file_prefix: str, url_prefix: str = "/files"):
    router = APIRouter(prefix=url_prefix)

    # 上传文件
    @router.post("/upload")
    def upload_file(
        file: UploadFile = File(...),
        uploadDir: str = Form(...),
        db: Session = Depends(get_db)
    ):
        os.makedirs(uploadDir, exist_ok=True)
         # 保存到本地
        file_location = os.path.join(uploadDir, file.filename)

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # 保存到数据库
        db_file = create_file(db, model_class, file.filename, f"{file_prefix}/{file.filename}")
        return {"file": db_file}

    # 删除文件
    @router.post("/delete-file")
    def delete_file_endpoint(
        filename: str = Form(...),
        uploadDir: str = Form(...),
        file_id: int = Form(...),
        db: Session = Depends(get_db)
    ):
        file_path = os.path.join(uploadDir, filename)
        if not os.path.exists(file_path):
            return {"success": False, "message": "文件不存在"}

        try:
            db_file = delete_file(db, model_class, file_id)
            os.remove(file_path)
            return {"success": True, "message": f"文件 {db_file} 已删除"}
        except Exception as e:
            return {"success": False, "message": f"删除失败: {str(e)}"}

    # 获取所有文件
    @router.get("/files")
    def get_files(db: Session = Depends(get_db)):
        files = get_all_files(db, model_class)
        return files

    # 清空文件和数据库记录
    @router.post("/clear-files")
    def clear_files(payload: dict, db: Session = Depends(get_db)):
        upload_dir = payload.get("uploadDir", "")
        if not os.path.exists(upload_dir):
            return {"success": False, "message": "目录不存在"}

        try:
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                os.remove(file_path)
            result = delete_all(db, model_class)
            return {"success": True, "message": f"{upload_dir} 下所有文件已清空"}
        except Exception as e:
            return {"success": False, "message": f"清空失败: {str(e)}"}
        

    return router
    