from typing import Optional, List
import pypdfium2 as pdfium
from PIL import Image
import os
import numpy as np

def trim_whitespace(image):
    """
    自动裁剪图片周围的白色空白区域
    """
    # 转换为灰度图
    gray = image.convert('L')
    
    # 转换为numpy数组
    img_array = np.array(gray)
    
    # 找到非白色区域的边界 (假设白色是255，允许一些误差)
    non_white_coords = np.where(img_array < 250)  # 250而不是255，允许一些灰色
    
    if len(non_white_coords[0]) == 0:
        # 如果整张图都是白色，返回原图
        return image
    
    # 找到内容的边界框
    top = np.min(non_white_coords[0])
    bottom = np.max(non_white_coords[0])
    left = np.min(non_white_coords[1])
    right = np.max(non_white_coords[1])
    
    # 添加一些边距（可选）
    margin = 10
    top = max(0, top - margin)
    bottom = min(img_array.shape[0], bottom + margin)
    left = max(0, left - margin)
    right = min(img_array.shape[1], right + margin)
    
    # 裁剪图片
    return image.crop((left, top, right, bottom))

def extract_pdf_pages(pdf_path: str, temp_dir: str):
    try:
        # 确保目标目录存在
        os.makedirs(temp_dir, exist_ok=True)
        
        pdf = pdfium.PdfDocument(pdf_path)
        image_paths = []

        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        # 遍历每一页
        for page_num in range(len(pdf)):
            # 渲染页面为图片
            page = pdf.get_page(page_num)
            
            # 获取页面尺寸
            width = page.get_width()
            height = page.get_height()
            
            # 计算合适的缩放比例，确保图片质量但不会太大
            # 目标：长边不超过2000像素
            max_dimension = max(width, height)
            if max_dimension > 0:
                scale = min(3.0, 2000 / max_dimension)  # 最大scale为3.0
            else:
                scale = 2.0
            
            # 渲染页面
            pil_image = page.render(
                scale=scale,
                rotation=0,
                crop=(0, 0, 0, 0),
                # 添加这些参数可以改善渲染质量
            ).to_pil()
            
            # 自动裁剪空白区域
            pil_image = trim_whitespace(pil_image)
            
            # 生成页面图片文件名
            image_filename = f"{base_filename}_page_{page_num + 1}.jpg"
            image_path = os.path.join(temp_dir, image_filename)
            
            # 保存为JPEG格式
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            pil_image.save(image_path, 'JPEG', quality=95, optimize=True)
            
            image_paths.append(image_path)
            print(f"已提取页面 {page_num + 1}: {image_path} (尺寸: {pil_image.size})")
            
        pdf.close()
        print(f"PDF页面提取完成，共提取 {len(image_paths)} 页")
        return image_paths
    except Exception as e:
        print(f"PDF页面提取失败: {str(e)}")
        return []

if __name__ == "__main__":
    pdf_path = "restored_00.pdf"
    temp_dir = "temp"
    
    # 检查PDF文件是否存在
    if not os.path.exists(pdf_path):
        print(f"错误：PDF文件 {pdf_path} 不存在")
    else:
        result = extract_pdf_pages(pdf_path, temp_dir)
        if result:
            print(f"成功提取 {len(result)} 个图片文件:")
            for img_path in result:
                print(f"  - {img_path}")
        else:
            print("PDF页面提取失败")