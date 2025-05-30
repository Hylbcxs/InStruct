from paddleocr import PaddleOCR
import json
import base64
import time
from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()
TEXT_DETECTION_MODEL = os.getenv("TEXT_DETECTION_MODEL")
TEXT_RECOGNITION_MODEL = os.getenv("TEXT_RECOGNITION_MODEL")
SAVE_JSON = "../ocr/output"

def get_top_left(box):
    return box[0][1], box[0][0]

def ocr_extract(prompt, img_url):

    # 初始化 PaddleOCR 实例
    ocr = PaddleOCR(
        text_detection_model_name="PP-OCRv5_server_det",
        text_detection_model_dir=TEXT_DETECTION_MODEL,
        text_recognition_model_name="PP-OCRv5_server_rec",
        text_recognition_model_dir=TEXT_RECOGNITION_MODEL,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False)

    # 对示例图像执行 OCR 推理 
    result = ocr.predict(
        input=img_url)

    # 可视化结果并保存 json 结果
    for res in result:
        res.save_to_json(SAVE_JSON)

    for filename in os.listdir(SAVE_JSON):
        json_path = os.path.join(SAVE_JSON, filename)
        with open(json_path, "r", encoding="utf-8") as f:
            ocr_data = json.load(f)
        os.remove(json_path)

    # 提取核心字段
    texts = ocr_data["rec_texts"]
    boxes = ocr_data["rec_polys"]

    # 1. 将所有内容按位置进行排序（从上到下、左到右）
    sorted_items = sorted(zip(texts, boxes), key=lambda x: get_top_left(x[1]))
    # 2. 构造带有位置信息的文本串（可帮助模型恢复结构）
    lines = []
    for idx, (text, box) in enumerate(sorted_items):
        x, y = box[0]
        # lines.append(f"[位置:({int(x)}, {int(y)})] {text}")
        lines.append(f"{idx+1}. {text}")
    # 构造结构化 OCR 信息列表
    ocr_lines = "\n".join(lines)
    parts = prompt.split("### 需要提取的字段：")
    prompt_start = parts[0]
    prompt_end = parts[1]
    # new_prompt = f"""
    # {prompt_start}
    # 以下是OCR识别到的文本内容，请优先基于图片信息进行字段提取，OCR提供的文本用于辅助理解不清晰的文本部分。
    # {ocr_lines}
    # ### 需要提取的字段：
    # {prompt_end}
    # """
    print(ocr_lines)
    new_prompt = prompt + "\n以下是ocr识别到的文本内容仅作为参考："+ocr_lines + "\n请确保字段尽可能完整、语义准确，保持 JSON 结构规范, 不要添加任何解释或文本说明。"

    return new_prompt