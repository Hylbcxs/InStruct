import os
import base64
from openai import OpenAI

def image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

document_type_identify = """
    请分析这张图片，识别这是哪种类型的单证。请从以下选项中选择一个：
    1. 发票 - 商业发票、税务发票等
    2. 合同 - 各类合同文件
    3. 报关单 - 海关报关相关文件
    4. 提单 - 运输提单等物流文件

    请只回答其中一个选项的中文名称，不要包含其他解释。
    """
client = OpenAI(
    base_url="https://api-inference.modelscope.cn/v1/",
    api_key="b628cfde-35e0-4f2f-85c7-38231c202ee3", # ModelScope Token
)
full_path = "/opt/data/private/hyl/code/InStruct/backend/upload/发票/发票.jpg"
response = client.chat.completions.create(
        # model='Qwen/Qwen2.5-VL-32B-Instruct',
        model='Qwen/Qwen2.5-VL-72B-Instruct',
        # model='qwen-vl-plus',
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image_url', 'image_url': {
                    'url': f"data:image/jpeg;base64,{image_to_base64(full_path)}"
                }},
                {'type': 'text', 'text': document_type_identify},
            ]
        }]
    )
print(response.choices[0].message.content)