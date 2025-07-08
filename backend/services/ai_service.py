import json
import re
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException
from utils.openai_utils import get_openai_client, get_default_model, get_upload_dir, get_prompt
from utils.image_utils import image_to_base64, validate_image_path
from ocr.myocr import ocr_extract

class AIService:
    def __init__(self):
        self.client = get_openai_client()
        self.model = get_default_model()
        self.upload_dir = get_upload_dir()
    
    def extract_fields_from_image(
        self, 
        image_url: str, 
        prompt: Optional[str] = None, 
        use_ocr: bool = True
    ) -> Dict[str, Any]:
        """从图片中提取字段信息"""
        try:
            # 验证图片路径
            full_path = validate_image_path(image_url, self.upload_dir)
            
            # 准备prompt
            if prompt is None:
                prompt = get_prompt("default_extract")
            
            # 处理OCR
            if use_ocr:
                full_prompt = ocr_extract(prompt, full_path)
                full_prompt = full_prompt.strip().replace(" ", "")
            else:
                full_prompt = prompt.strip().replace(" ", "") + "\n请确保字段尽可能完整、语义准确，保持 JSON 结构规范, 不要添加任何解释或文本说明。"
            
            # 调用AI模型
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image_url', 
                            'image_url': {
                                'url': f"data:image/jpeg;base64,{image_to_base64(full_path)}"
                            }
                        },
                        {'type': 'text', 'text': full_prompt},
                    ]
                }]
            )
            
            # 解析响应
            content = response.choices[0].message.content
            print(f"AI响应内容: {content}")
            
            return self._parse_json_response(content)
            
        except Exception as e:
            print(f"字段提取失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"字段提取失败: {str(e)}")
    
    def identify_document_type(self, image_url: str) -> str:
        """识别单证类型"""
        try:
            
            # 获取识别prompt
            prompt = get_prompt("document_type_identify")
            
            # 调用AI模型
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f"data:image/jpeg;base64,{image_to_base64(image_url)}"
                            }
                        },
                        {'type': 'text', 'text': prompt}
                    ]
                }],
                max_tokens=10,
                temperature=0.1
            )
            
            # 解析识别结果
            identified_type = response.choices[0].message.content.strip()
            
            # 验证识别结果
            valid_types = ['发票', '合同', '报关单', '提单']
            if identified_type not in valid_types:
                # 尝试匹配
                for valid_type in valid_types:
                    if valid_type in identified_type:
                        return valid_type
                # 默认返回发票
                return '其他'
            
            return identified_type
            
        except Exception as e:
            print(f"单证类型识别失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"单证类型识别失败: {str(e)}")
    
    def extract_fields_by_document_type(
        self, 
        image_url: str, 
        document_type: str, 
        use_ocr: bool = True
    ) -> Dict[str, Any]:
        """根据单证类型提取字段"""
        prompt_map = {
            '发票': get_prompt("invoice_extract"),
            '合同': get_prompt("default_extract"),  # 可以后续添加专门的合同prompt
            '报关单': get_prompt("default_extract"),  # 可以后续添加专门的报关单prompt
            '提单': get_prompt("default_extract")  # 可以后续添加专门的提单prompt
        }
        
        prompt = prompt_map.get(document_type, get_prompt("default_extract"))
        return self.extract_fields_from_image(image_url, prompt, use_ocr)
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析AI响应中的JSON内容"""
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试从markdown代码块中提取
            json_match = re.search(r'```json\n([\s\S]*?)\n```', content)
            if json_match:
                json_content = json_match.group(1)
                return json.loads(json_content)
            else:
                # 尝试从普通代码块中提取
                json_match = re.search(r'```\n([\s\S]*?)\n```', content)
                if json_match:
                    json_content = json_match.group(1)
                    return json.loads(json_content)
                else:
                    raise ValueError("模型输出中未找到有效的 JSON 内容")

# 创建全局实例
ai_service = AIService()