import base64
import os
from typing import Optional, List, Tuple
from fastapi import HTTPException

import pypdfium2 as pdfium
from PIL import Image, ExifTags
import numpy as np

import zipfile
import shutil

from ocr.myocr import ocr_extract_with_orientation

def should_skip_file(filename: str) -> bool:
    """检查是否应该跳过该文件"""
    # 获取文件名（不包含路径）
    basename = os.path.basename(filename)
    
    # 跳过条件
    skip_conditions = [
        basename.startswith('._'),          # macOS系统文件
        basename.startswith('.DS_Store'),   # macOS文件夹配置文件
        basename.startswith('Thumbs.db'),   # Windows缩略图文件
        basename.startswith('.'),           # 其他隐藏文件
        '__MACOSX' in filename,             # macOS压缩包元数据文件夹
        basename == '',                     # 空文件名
        len(basename) == 0,                 # 空文件名
    ]
    
    return any(skip_conditions)

def image_to_base64(file_path: str) -> str:
    """将图片文件转换为base64编码"""
    try:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"图片文件不存在: {file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片转换失败: {str(e)}")

def validate_image_path(image_url: str, upload_dir: str) -> str:
    """验证并返回完整的图片路径"""
    if not image_url:
        raise HTTPException(status_code=400, detail="缺少图片路径")
    
    # 构造完整路径
    full_path = os.path.join(upload_dir, image_url.lstrip("/"))
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"图片不存在: {full_path}")
    
    return full_path

def is_image_file(filename: str) -> bool:
    """检查文件是否为图片格式"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    return os.path.splitext(filename.lower())[1] in image_extensions

def get_file_type(filename: str) -> str:
    """获取文件类型"""
    extension = os.path.splitext(filename.lower())[1]
    
    if extension in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}:
        return 'image'
    elif extension == '.pdf':
        return 'pdf'
    elif extension in {'.zip', '.rar', '.7z'}:
        return 'archive'
    else:
        return 'unknown'

def trim_whitespace(image):
    """
    自动裁剪图片周围的白色空白区域
    """
    # 转换为灰度图
    gray = image.convert('L')
    # 转换为numpy数组
    img_array = np.array(gray)
    # 找到非白色区域的边界
    non_white_coords = np.where(img_array < 250) 
    if len(non_white_coords[0]) == 0:
        # 如果整张图都是白色，返回原图
        return image
    
    # 找到内容的边界框
    top = np.min(non_white_coords[0])
    bottom = np.max(non_white_coords[0])
    left = np.min(non_white_coords[1])
    right = np.max(non_white_coords[1])
    # 添加边距
    margin = 10
    top = max(0, top - margin)
    bottom = min(img_array.shape[0], bottom + margin)
    left = max(0, left - margin)
    right = min(img_array.shape[1], right + margin)
    
    # 裁剪图片
    return image.crop((left, top, right, bottom))

def extract_pdf_pages(pdf_path: str, temp_dir: str) -> List[str]:
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        image_paths = []

        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        # 遍历每一页
        for page_num in range(len(pdf)):
            # 渲染页面为图片
            page = pdf.get_page(page_num)
            # 页面大小
            width = page.get_width()
            height = page.get_height()
            # 计算合适的缩放比例
            max_dimension = max(width, height)
            if max_dimension > 0:
                scale = min(3.0, 2000 / max_dimension)  # 最大scale为3.0
            else:
                scale = 2.0
            pil_image = page.render(
                scale=scale,  # 提高分辨率
                rotation=0,
                crop=(0, 0, 0, 0)
            ).to_pil()
            # 自动裁剪空白区域
            pil_image = trim_whitespace(pil_image)
            
            # 生成页面图片文件名
            image_filename = f"{base_filename}_page_{page_num + 1}.jpg"
            image_path = os.path.join(temp_dir, image_filename)
            
            # 保存为JPEG格式
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            pil_image.save(image_path, 'JPEG', quality=95)
            
            image_paths.append(image_path)
            
        pdf.close()
        return image_paths
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF页面提取失败: {str(e)}")

def extract_archive_files(archive_path: str, temp_dir: str) -> List[str]:
    """提取压缩包中的所有文件"""
    try:
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)

        image_paths = []
        if archive_path.lower().endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # 解压所有文件
                for zip_info in zip_ref.infolist():
                    # 过滤不正常的文件
                    if should_skip_file(zip_info.filename):
                        continue
                        
                    fixed_name = zip_info.filename.encode('cp437').decode('utf-8')
                    zip_info.filename = fixed_name
                    zip_ref.extract(zip_info, extract_dir)
                
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        # 过滤不正常的文件
                        if should_skip_file(file):
                            continue
                            
                        file_path = os.path.join(root, file)
                        file_type = get_file_type(file)
                        
                        if file_type == 'image':
                            # 直接复制图片文件到临时目录
                            new_filename = f"archive_{len(image_paths) + 1}_{file}"
                            new_path = os.path.join(temp_dir, new_filename)
                            shutil.copy2(file_path, new_path)
                            image_paths.append(new_path)
                            
                        elif file_type == 'pdf':
                            # 将PDF转换为图片
                            try:
                                pdf_images = extract_pdf_pages(file_path, temp_dir)
                                for i, pdf_image_path in enumerate(pdf_images):
                                    # 重命名PDF页面文件
                                    base_name = os.path.splitext(file)[0]
                                    new_filename = f"archive_pdf_{len(image_paths) + 1}_{base_name}_page_{i + 1}.jpg"
                                    new_path = os.path.join(temp_dir, new_filename)
                                    shutil.move(pdf_image_path, new_path)
                                    image_paths.append(new_path)
                            except Exception as e:
                                print(f"处理PDF文件 {file} 失败: {str(e)}")
                                continue
        else:
            print(f"不支持的压缩包格式: {archive_path}")
            return []  
        return image_paths
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"压缩包提取失败: {str(e)}")
