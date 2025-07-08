from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from database.database import Base
from models.file_models import InvoiceModel, DeclarationModel, ContractModel, LandingModel
from utils.image_utils import (
    get_file_type, 
    is_image_file, 
    extract_pdf_pages, 
    extract_archive_files,
    process_image_with_orientation_correction
)
from services.file_service import create_file
from services.ai_service import ai_service

from typing import Type, Any

import os
import shutil
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=3) 
    
TABLE_MODELS = {
    "发票": InvoiceModel,
    "合同": ContractModel, 
    "报关单": DeclarationModel,
    "提单": LandingModel
}
TABLE_NAMES = {
    "invoice": "发票",
    "contract": "合同",
    "declaration": "报关单",
    "landing": "提单"
}
UPLOAD_DIR_MAP = {
    '发票': '../backend/upload/发票',
    '合同': '../backend/upload/合同',
    '报关单': '../backend/upload/报关单',
    '提单': '../backend/upload/提单'
    }

def get_table_files_counts(db: Session):
    """"
    获取所有模型表的记录数量
    """
    tables = Base.metadata.tables.keys()
    item_list = []
    table_counts = {}
    counts = 0

    for table in tables:
        try:
            count = db.query(Base.metadata.tables[table]).count()
            counts += count
            table_name = TABLE_NAMES.get(table)
            table_counts[table_name] = count
        except Exception as e:
            table_name = TABLE_NAMES.get(table)
            print(f"获取表 {table_name} 的记录数失败: {str(e)}")
            table_counts[table_name] = 0
    return table_counts, counts

def get_all_table_records(db: Session):
    """
    获取所有模型表记录
    """
    all_records = []
    for table_name, model_class in TABLE_MODELS.items():
        try:
            records = db.query(model_class).all()
            for record in records:
                all_records.append({
                    "id": record.id,
                    "name": record.name,
                    "thumbnail": record.thumbnail,
                    "check": record.check,
                    "type": table_name,
                    "ExtractedDefaultField": record.ExtractedDefaultField,
                    "ExtractedCustomField": record.ExtractedCustomField,
                    "loading_auto": record.loading_auto,
                    "upload_date": record.created_at.strftime("%Y/%m/%d") if record.created_at else "",
                    "modified_date": record.modified_at.strftime("%Y/%m/%d") if record.modified_at else ""
                })
        except Exception as e:
            print(f"获取表 {table_name} 的记录失败: {str(e)}")
            continue
    
    return all_records

async def smart_upload(
    db: Session,
    file: UploadFile = File(...),
):
    loop = asyncio.get_running_loop()
    try:
        file_type = get_file_type(file.filename)

        if file_type == 'image':
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, file.filename)
                with open(temp_file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                print(f"临时图片路径: {temp_file_path}")

                # 图片方向检测和校正
                corrected_image_path = process_image_with_orientation_correction(temp_file_path, temp_dir)
                print(f"方向校正后图片路径: {corrected_image_path}")

                saved_files = []
                # 判断类型 (在校正后的图片上进行识别)
                document_type = await loop.run_in_executor(executor, ai_service.identify_document_type, corrected_image_path)
                model_class = TABLE_MODELS.get(document_type)
                uploadDir = UPLOAD_DIR_MAP.get(document_type)
                if uploadDir is None:
                    return saved_files
                os.makedirs(uploadDir, exist_ok=True)
                # 保存校正后的图片到本地
                file_location = os.path.join(uploadDir, file.filename)
                shutil.copy2(corrected_image_path, file_location)
            
            # 保存到数据库
            if model_class is not None:
                db_file = create_file(db, model_class, file.filename, f"/{document_type}/{file.filename}")
                saved_files.append((db_file, document_type))
            return saved_files
        
        elif file_type == 'pdf':
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_pdf_path = os.path.join(temp_dir, file.filename)
                with open(temp_pdf_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                print(f"pdf临时路径: {temp_pdf_path}")
                page_image_paths = extract_pdf_pages(temp_pdf_path, temp_dir)

                if not page_image_paths:
                    return []
                saved_files = []
                for i, page_image_path in enumerate(page_image_paths):
                    try:
                        # 对PDF页面图片进行方向检测和校正
                        corrected_page_path = process_image_with_orientation_correction(page_image_path, temp_dir)
                        print(f"PDF第{i+1}页方向校正: {page_image_path} -> {corrected_page_path}")
                        
                        # 对校正后的页面进行文档类型识别
                        document_type = await loop.run_in_executor(executor, ai_service.identify_document_type, corrected_page_path)
                        model_class = TABLE_MODELS.get(document_type)
                        uploadDir = UPLOAD_DIR_MAP.get(document_type)
                        
                        if uploadDir is None:
                            print(f"未识别的文档类型: {document_type}")
                            continue
                            
                        os.makedirs(uploadDir, exist_ok=True)
                        
                        # 生成页面文件名
                        base_filename = os.path.splitext(file.filename)[0]
                        page_filename = f"{base_filename}_page_{i + 1}.jpg"
                        file_location = os.path.join(uploadDir, page_filename)
                        
                        # 保存校正后的页面图片到指定目录
                        shutil.copy2(corrected_page_path, file_location)
                        
                        # 保存到数据库
                        if model_class is not None:
                            db_file = create_file(db, model_class, page_filename, f"/{document_type}/{page_filename}")
                            saved_files.append((db_file, document_type))
                            
                    except Exception as e:
                        print(f"处理PDF第{i+1}页失败: {str(e)}")
                        continue
            return saved_files
        elif file_type == 'archive':
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_archive_path = os.path.join(temp_dir, file.filename)
                with open(temp_archive_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                print(f"压缩包临时路径: {temp_archive_path}")

                archive_image_files = extract_archive_files(temp_archive_path, temp_dir)
                if not archive_image_files:
                    return []
                saved_files = []
                for i, image_path in enumerate(archive_image_files):
                    try:
                        print(f"正在处理压缩包文件 {i+1}: {image_path}")
                        
                        # 对每个图片进行文档类型识别
                        # document_type = await loop.run_in_executor(executor, ai_service.identify_document_type, image_path)
                        document_type = ai_service.identify_document_type(image_path)
                        print(f"文件 {image_path} 识别结果: {document_type}")
                        
                        model_class = TABLE_MODELS.get(document_type)
                        uploadDir = UPLOAD_DIR_MAP.get(document_type)
                        
                        print(f"model_class: {model_class}, uploadDir: {uploadDir}")
                        
                        if uploadDir is None:
                            print(f"未识别的文档类型: {document_type}")
                            continue
                            
                        os.makedirs(uploadDir, exist_ok=True)
                        
                        # 使用压缩包名作为前缀生成新文件名
                        base_archive_name = os.path.splitext(file.filename)[0]
                        new_filename = f"{base_archive_name}_page_{i+1}.jpg"
                        
                        file_location = os.path.join(uploadDir, new_filename)
                        
                        # 保存图片到指定目录
                        shutil.copy2(image_path, file_location)
                        
                        # 保存到数据库
                        if model_class is not None:
                            db_file = create_file(db, model_class, new_filename, f"/{document_type}/{new_filename}")
                            saved_files.append((db_file, document_type))
                            print(f"✅ 成功保存文件: {new_filename}, 类型: {document_type}, ID: {db_file.id}")
                        else:
                            print(f"❌ model_class为None，无法保存文件: {new_filename}")

                            
                    except Exception as e:
                        print(f"❌ 处理压缩包文件 {image_path} 失败: {str(e)}")
                        continue
            print("saved_files",saved_files)
            return saved_files
    except Exception as e:
        return []
