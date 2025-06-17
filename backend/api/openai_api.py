from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from database.database import get_db
from ocr.myocr import ocr_extract

from openai import OpenAI

from dotenv import load_dotenv
import base64
import os
import re
import json
from concurrent.futures import ThreadPoolExecutor
import asyncio

executor = ThreadPoolExecutor(max_workers=3) 
router = APIRouter(prefix="/api")

# 加载 .env 文件中的环境变量
load_dotenv()
client = OpenAI(
    base_url=os.getenv("API_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"), # ModelScope Token
)
def image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def sync_extract_logic(payload: dict):
    prompt = """
    请分析图片内容，并提取其中包含的所有字段及对应的值，以 JSON 格式输出。
    要求如下：
    1. 每个字段作为 JSON 的一个键；
    2. 每个字段的值为图片中对应的语义内容；
    3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
    4. 不需要包含位置信息、类型或其他元数据；
    5. 注意：请只输出 JSON，不要添加任何解释或文本说明，也不要使用 Markdown 包裹！格式示例：
    {
    "姓名": "张三",
    "性别": "男",
    "学历信息": {
        "学校": "清华大学",
        "专业": "计算机科学",
        "学历": "本科"
    },
    "工作经历": {
        "公司": "字节跳动",
        "职位": "前端工程师"
    }
    }
    请确保字段尽可能完整、语义准确，保持 JSON 结构规范。
    """
    image_url = payload.get("image_url", "")
    InvoicePrompt = payload.get("prompt", prompt)
    use_ocr = payload.get("use_ocr", True)

    if not image_url:
        raise HTTPException(status_code=400, detail="缺少图片路径")

    # 构造完整路径（假设图片放在 public 下）
    full_path = os.path.join(os.getenv("UPLOAD_DIR"), image_url.lstrip("/"))

    if not os.path.exists(full_path):
        raise HTTPException(status_code=400, detail="图片不存在")
    
    # 调用模型
    if use_ocr:
        full_prompt = ocr_extract(InvoicePrompt, full_path)
        full_prompt = full_prompt.strip().replace(" ","")
    else:
        full_prompt = InvoicePrompt.strip().replace(" ","") + "\n请确保字段尽可能完整、语义准确，保持 JSON 结构规范, 不要添加任何解释或文本说明。"
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
                {'type': 'text', 'text': full_prompt},
            ]
        }]
    )
    # return StreamingResponse(response.choices[0].message.content, media_type="application/json")
    content = response.choices[0].message.content
    print(content)
    json_match = re.search(r'```json\n([\s\S]*?)\n```', content)
    if json_match:
        json_content = json_match.group(1)
        parsed_json = json.loads(json_content)
        print(parsed_json)
        return parsed_json
    else:
        raise ValueError("模型输出中未找到 JSON 内容")
     

@router.post("/extract")
async def extract_fields(payload: dict):
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(executor, sync_extract_logic, payload)
        return JSONResponse(content=result, media_type="application/json")
    except Exception as e:
        print("Error during threaded model call:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    # prompt = """
    # 请分析图片内容，并提取其中包含的所有字段及对应的值，以 JSON 格式输出。
    # 要求如下：
    # 1. 每个字段作为 JSON 的一个键；
    # 2. 每个字段的值为图片中对应的语义内容；
    # 3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
    # 4. 不需要包含位置信息、类型或其他元数据；
    # 5. 注意：请只输出 JSON，不要添加任何解释或文本说明，也不要使用 Markdown 包裹！格式示例：
    # {
    # "姓名": "张三",
    # "性别": "男",
    # "学历信息": {
    #     "学校": "清华大学",
    #     "专业": "计算机科学",
    #     "学历": "本科"
    # },
    # "工作经历": {
    #     "公司": "字节跳动",
    #     "职位": "前端工程师"
    # }
    # }
    # 请确保字段尽可能完整、语义准确，保持 JSON 结构规范。
    # """
    # image_url = payload.get("image_url", "")
    # InvoicePrompt = payload.get("prompt", prompt)
    # use_ocr = payload.get("use_ocr", True)

    # if not image_url:
    #     raise HTTPException(status_code=400, detail="缺少图片路径")

    # # 构造完整路径（假设图片放在 public 下）
    # full_path = os.path.join(os.getenv("UPLOAD_DIR"), image_url.lstrip("/"))

    # if not os.path.exists(full_path):
    #     raise HTTPException(status_code=400, detail="图片不存在")
    
    # # 调用模型
    # if use_ocr:
    #     full_prompt = ocr_extract(InvoicePrompt, full_path)
    #     full_prompt = full_prompt.strip().replace(" ","")
    # else:
    #     full_prompt = InvoicePrompt.strip().replace(" ","") + "\n请确保字段尽可能完整、语义准确，保持 JSON 结构规范, 不要添加任何解释或文本说明。"
    # try:
    #     response = client.chat.completions.create(
    #         # model='Qwen/Qwen2.5-VL-32B-Instruct',
    #         model='Qwen/Qwen2.5-VL-32B-Instruct',
    #         # model='qwen-vl-plus',
    #         messages=[{
    #             'role': 'user',
    #             'content': [
    #                 {'type': 'image_url', 'image_url': {
    #                     'url': f"data:image/jpeg;base64,{image_to_base64(full_path)}"
    #                 }},
    #                 {'type': 'text', 'text': full_prompt},
    #             ]
    #         }]
    #     )
    #     # return StreamingResponse(response.choices[0].message.content, media_type="application/json")
    #     content = response.choices[0].message.content
    #     print(content)
    #     json_match = re.search(r'```json\n([\s\S]*?)\n```', content)
    #     if json_match:
    #         json_content = json_match.group(1)
    #         parsed_json = json.loads(json_content)
    #         print(parsed_json)
    
    #         # save_output = re.sub(r'\.(jpe?g|png)$', fr'_useocr_{use_ocr}.json', image_url)
    #         # with open(f"/opt/data/private/hyl/code/InStruct/backend/output{save_output}","w", encoding="utf-8") as f:
    #         #     json.dump(parsed_json, f, ensure_ascii=False, indent=4)
    #         return JSONResponse(content=parsed_json, media_type="application/json")

    # except Exception as e:
    #     print("Error during model call:", str(e))  # 添加这行
    #     raise HTTPException(status_code=500, detail=str(e))