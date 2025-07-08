import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

def get_openai_client() -> OpenAI:
    """获取OpenAI客户端实例"""
    return OpenAI(
        base_url=os.getenv("API_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

def get_default_model() -> str:
    """获取默认模型名称"""
    return os.getenv("DEFAULT_MODEL", "Qwen/Qwen2.5-VL-72B-Instruct")

def get_upload_dir() -> str:
    """获取上传目录"""
    return os.getenv("UPLOAD_DIR", "../backend/upload")

PROMPTS = {
    "default_extract": """
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
        """,
    "document_type_identify": """
        请分析这张图片，识别这是哪种类型的单证。请从以下选项中选择一个：
        1. 发票 - 商业发票、税务发票等
        2. 合同 - 各类合同文件
        3. 报关单 - 海关报关相关文件
        4. 提单 - 运输提单等物流文件

        请只回答其中一个选项的中文名称，不要包含其他解释。
        """,
}

def get_prompt(prompt_type: str = "default_extract") -> str:
    """获取预定义的prompt"""
    return PROMPTS.get(prompt_type, PROMPTS["default_extract"])