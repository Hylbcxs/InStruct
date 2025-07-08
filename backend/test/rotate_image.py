from PIL import Image, ExifTags
import numpy as np
import shutil
import os
from paddleocr import DocImgOrientationClassification
import json

SAVE_JSON = "./temp"

def ocr_extract_with_orientation(img_url):
    model = DocImgOrientationClassification(model_dir="/opt/data/private/hyl/code/InStruct/model/ocr_model/PP-LCNet_x1_0_doc_ori")
    output = model.predict(img_url,  batch_size=1)
    for res in output:
        res.save_to_json(SAVE_JSON)

    for filename in os.listdir(SAVE_JSON):
        json_path = os.path.join(SAVE_JSON, filename)
        with open(json_path, "r", encoding="utf-8") as f:
            ocr_data = json.load(f)
        os.remove(json_path)

    label_names = ocr_data["label_names"]
    return label_names[0]

def auto_rotate_image(image_path: str, output_path: str = None) -> str:
    try:
        if output_path is None:
            output_path = image_path
            
        # 检测需要旋转的角度
        rotation_angle = ocr_extract_with_orientation(image_path)
        
        if rotation_angle == 0:
            print("图片方向正常，无需旋转")
            if output_path != image_path:
                shutil.copy2(image_path, output_path)
            return output_path
        
        # 打开图片并旋转
        image = Image.open(image_path)
        image.show()
        
        # 旋转图片（PIL中正角度为逆时针）
        if rotation_angle == 90:
            rotated_image = image.rotate(90, expand=True)
        elif rotation_angle == 180:
            rotated_image = image.rotate(180, expand=True)
        elif rotation_angle == 270:
            rotated_image = image.rotate(-90, expand=True)
        else:
            rotated_image = image
        
        # 保存图片
        if rotated_image.mode != 'RGB':
            rotated_image = rotated_image.convert('RGB')
        rotated_image.save(output_path, 'JPEG', quality=95)
        
        print(f"图片已旋转{rotation_angle}度并保存到: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"图片旋转失败: {str(e)}")
        # 如果旋转失败，至少复制原图
        if output_path != image_path:
            shutil.copy2(image_path, output_path)
        return output_path

auto_rotate_image(image_path="合同r.jpg")