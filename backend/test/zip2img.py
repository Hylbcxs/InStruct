import os
from zipfile import ZipFile
import shutil
from typing import List, Tuple
from pdf2image import extract_pdf_pages

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

def extract_archive_files(archive_path: str, temp_dir: str):
    """提取压缩包中的所有文件"""
    try:
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)

        image_paths = []
        if archive_path.lower().endswith('.zip'):
            with ZipFile(archive_path, 'r') as zip_ref:
                for zip_info in zip_ref.infolist():
                    fixed_name = zip_info.filename.encode('cp437').decode('utf-8')
                    zip_info.filename = fixed_name
                    zip_ref.extract(zip_info, extract_dir)
                
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        print(file)
                        
                        # 过滤不正常的文件
                        if should_skip_file(file):
                            print(f"⏭️  跳过系统文件: {file}")
                            continue
                            
                        file_path = os.path.join(root, file)
                        file_type = get_file_type(file)
                        
                        if file_type == 'image':
                            # 直接复制图片文件到临时目录
                            new_filename = f"archive_{len(image_paths) + 1}_{file}"
                            new_path = os.path.join(temp_dir, new_filename)
                            shutil.copy2(file_path, new_path)
                            image_paths.append((new_path, file))
                            
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
                                    image_paths.append((new_path, f"{file}_page_{i + 1}"))
                            except Exception as e:
                                print(f"处理PDF文件 {file} 失败: {str(e)}")
                                continue
        else:
            print(f"不支持的压缩包格式: {archive_path}")  
        return image_paths
    except Exception as e:
        print(f"压缩包提取失败: {str(e)}")


if __name__ == "__main__":
    archive_path = "test.zip"
    temp_dir = "temp"
    extract_archive_files(archive_path, temp_dir)