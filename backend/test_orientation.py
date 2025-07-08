#!/usr/bin/env python3
"""
图片方向检测和自动旋转功能测试脚本
"""

import os
import sys
from PIL import Image

# 添加backend路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.image_utils import (
    detect_image_orientation,
    auto_rotate_image,
    process_image_with_orientation_correction,
    get_image_orientation_from_exif
)

def test_orientation_detection():
    """测试图片方向检测功能"""
    print("=== 图片方向检测功能测试 ===\n")
    
    # 示例图片路径（请替换为实际存在的图片路径）
    test_image_paths = [
        "upload/发票/test_image.jpg",  # 请替换为实际图片路径
        "upload/合同/test_contract.jpg",
        # 添加更多测试图片...
    ]
    
    for image_path in test_image_paths:
        if not os.path.exists(image_path):
            print(f"图片不存在，跳过: {image_path}")
            continue
            
        print(f"检测图片: {image_path}")
        
        # 1. EXIF方向检测
        print("1. EXIF方向检测:")
        exif_orientation = get_image_orientation_from_exif(image_path)
        print(f"   EXIF方向值: {exif_orientation}")
        
        # 2. 综合方向检测
        print("2. 综合方向检测:")
        rotation_needed = detect_image_orientation(image_path, method="auto")
        print(f"   需要旋转角度: {rotation_needed}度")
        
        # 3. OCR方向检测（如果可用）
        print("3. OCR方向检测:")
        ocr_rotation = detect_image_orientation(image_path, method="ocr")
        print(f"   OCR建议旋转角度: {ocr_rotation}度")
        
        print("-" * 50)

def test_auto_rotation():
    """测试自动旋转功能"""
    print("\n=== 自动旋转功能测试 ===\n")
    
    test_image = "upload/发票/test_image.jpg"  # 请替换为实际图片路径
    
    if not os.path.exists(test_image):
        print(f"测试图片不存在: {test_image}")
        return
    
    print(f"测试图片: {test_image}")
    
    # 获取原始图片信息
    original_image = Image.open(test_image)
    print(f"原始图片尺寸: {original_image.size}")
    
    # 创建输出目录
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 自动检测并旋转
    corrected_path = os.path.join(output_dir, "auto_corrected.jpg")
    result_path = auto_rotate_image(test_image, corrected_path, method="auto")
    print(f"自动校正后图片保存到: {result_path}")
    
    # 2. 仅使用EXIF信息旋转
    exif_corrected_path = os.path.join(output_dir, "exif_corrected.jpg")
    result_path = auto_rotate_image(test_image, exif_corrected_path, method="exif")
    print(f"EXIF校正后图片保存到: {result_path}")
    
    # 3. 仅使用OCR检测旋转
    ocr_corrected_path = os.path.join(output_dir, "ocr_corrected.jpg")
    result_path = auto_rotate_image(test_image, ocr_corrected_path, method="ocr")
    print(f"OCR校正后图片保存到: {result_path}")

def test_batch_processing():
    """测试批量处理功能"""
    print("\n=== 批量处理功能测试 ===\n")
    
    input_dir = "upload/发票"  # 请替换为实际目录
    output_dir = "corrected_images"
    
    if not os.path.exists(input_dir):
        print(f"输入目录不存在: {input_dir}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理目录中的所有图片
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    processed_count = 0
    
    for filename in os.listdir(input_dir):
        if os.path.splitext(filename.lower())[1] in image_extensions:
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"corrected_{filename}")
            
            print(f"处理: {filename}")
            result_path = process_image_with_orientation_correction(input_path, output_dir)
            print(f"   -> {result_path}")
            processed_count += 1
    
    print(f"\n批量处理完成，共处理 {processed_count} 张图片")

def create_test_rotated_images():
    """创建测试用的旋转图片"""
    print("\n=== 创建测试旋转图片 ===\n")
    
    original_image = "upload/发票/test_image.jpg"  # 请替换为实际图片路径
    
    if not os.path.exists(original_image):
        print(f"原始图片不存在: {original_image}")
        return
    
    output_dir = "test_rotated_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建不同角度的旋转图片用于测试
    image = Image.open(original_image)
    
    rotations = [
        (0, "normal"),
        (90, "rotated_90"),
        (180, "rotated_180"),
        (270, "rotated_270")
    ]
    
    for angle, suffix in rotations:
        if angle == 0:
            rotated = image
        else:
            rotated = image.rotate(-angle, expand=True)
        
        output_path = os.path.join(output_dir, f"test_{suffix}.jpg")
        if rotated.mode != 'RGB':
            rotated = rotated.convert('RGB')
        rotated.save(output_path, 'JPEG', quality=95)
        print(f"创建测试图片: {output_path}")

if __name__ == "__main__":
    print("图片方向检测和自动旋转功能测试")
    print("=" * 50)
    
    # 运行测试
    try:
        # 1. 方向检测测试
        test_orientation_detection()
        
        # 2. 自动旋转测试
        test_auto_rotation()
        
        # 3. 批量处理测试
        test_batch_processing()
        
        # 4. 创建测试图片（可选）
        # create_test_rotated_images()
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n测试完成！") 