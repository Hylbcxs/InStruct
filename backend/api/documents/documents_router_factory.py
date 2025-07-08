from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from services.document_service import get_table_files_counts, get_all_table_records, smart_upload

from typing import Type, Any


def create_documents_router(url_prefix: str = "/documents"):
    router = APIRouter(prefix=url_prefix)

    @router.get("/total-records")
    def get_total_records(db: Session = Depends(get_db)):
        table_counts, counts = get_table_files_counts(db)
        return {"total_records": table_counts, "counts": counts}

    @router.get("/all-records")
    def get_all_records(db: Session = Depends(get_db)):
        records = get_all_table_records(db)
        return {"records": records}
    
    @router.post("/smart-upload")
    async def smart_upload_endpoint(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        saved_files = await smart_upload(db, file)
        if saved_files:
            for file in saved_files:
                print(file[0].id)
        return {"file": saved_files}
    
    return router