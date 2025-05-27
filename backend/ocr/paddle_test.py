from paddleocr import PaddleOCR
import json
import base64
import time
from openai import OpenAI
from prompts import *
start_time = time.time()
# 初始化 PaddleOCR 实例
ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_server_det",
    text_recognition_model_name="PP-OCRv5_server_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False)

def image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def get_top_left(box):
    return box[0][1], box[0][0]

img_url = "/opt/data/private/hyl/code/InStruct/frontend/public/发票/发票.jpg"

# 对示例图像执行 OCR 推理 
result = ocr.predict(
    input=img_url)

# 可视化结果并保存 json 结果
for res in result:
    res.print()
    res.save_to_img("./output")
    res.save_to_json("./output")

json_path = "./output/发票_res.json"

with open(json_path, "r", encoding="utf-8") as f:
    ocr_data = json.load(f)

# 提取核心字段
texts = ocr_data["rec_texts"]
scores = ocr_data["rec_scores"]
boxes = ocr_data["rec_polys"]

# 1. 将所有内容按位置进行排序（从上到下、左到右）
sorted_items = sorted(zip(texts, boxes), key=lambda x: get_top_left(x[1]))
# 2. 构造带有位置信息的文本串（可帮助模型恢复结构）
lines = []
for idx, (text, box) in enumerate(sorted_items):
    x, y = box[0]
    lines.append(f"[位置:({int(x)}, {int(y)})] {text}")
print(lines)
# 构造结构化 OCR 信息列表
ocr_text = "\n".join(lines)


# prompt = INVOICE_PROMPT.format(ocr_text=ocr_text)
prompt = """
请分析图片内容和ocr识别结果，提取其中包含的所有指定字段及对应的值，并以 JSON 格式输出。

要求如下：
1. 每个字段作为 JSON 的一个键；
2. 每个字段的值为图片中对应的语义内容；
3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
4. 不需要包含位置信息、类型或其他元数据；
5. 注意：请只输出 JSON，不要添加任何解释或文本说明， 确保字段尽可能完整、语义准确, 保持 JSON 结构规范;

### 需要提取的字段：
- **单据种类**
- **发票编号**
- **发票日期**
- **卖方信息**：包括
    - 公司名称：优先识别中文公司名
    - 地址
    - 电话(Tel)
    - 传真(Fax)
- **买方信息**：包括：
    - 公司名称：优先识别中文公司名
    - 地址
    - 电话(Tel)
    - 传真(Fax)
- **货物信息**：如果有多条货物信息，用数组存储，每条货物信息是一个对象,包括：
    - 货物名称: 只提取货物名称，不包含机型、规格等附加信息
    - 数量
    - 单价
    - 总价
- **货物总数量**: 所有货物的数量之和
- **货物总价**: 所有货物的总价之和

### 示例输出格式：
{
    "单据种类": "INVOICE",
    "发票编号": "023746123",
    "发票日期": "2020/01/01",
    "卖方信息": {
    "公司名称": "Seller Company",
    "地址": "Suzhou city, Jiangsu province",
    "电话": "15062330857",
    "传真": "2649412"
    },
    "买方信息": {
    "公司名称": "Buyer Company",
    "地址": "Suzhou city, Jiangsu province",
    "电话": "15062330857",
    "传真": "2649412"
    },
    "货物信息": [
    {
        "货物名称": "Flower",
        "数量": "10,000",
        "单价": "0.01 USD",
        "总价": "100 USD"
    },
    {
        "货物名称": "其他商品",
        "数量": "100",
        "单价": "10 USD",
        "总价": "1000 USD"
    }
    ],
    "货物总数量": “10,100”,
    "货物总价格": ”1100 USD“,
}
"""
# prompt = prompt.replace("{ocr_content}", ocr_text.strip())
prompt = prompt + "ocr识别结果如下" + ocr_text
print(prompt)
client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1/',
    api_key='d0d1ec43-af89-4d9c-bf5e-c5edd1f600fe', # ModelScope Token
)

response = client.chat.completions.create(
    model='Qwen/Qwen2.5-VL-32B-Instruct', # ModelScope Model-Id
    messages=[{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {
                'url': f"data:image/jpeg;base64,{image_to_base64(img_url)}"
            }},
        ]
    }]
)
print(response.choices[0].message.content)
# for chunk in response:
#     if chunk.choices[0].delta.content is not None:
#         print(chunk.choices[0].delta.content, end='', flush=True)
