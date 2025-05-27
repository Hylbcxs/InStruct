from pydantic import BaseModel
from typing import List, Dict, Optional
import difflib


EXACT_MATCH_FIELDS = {
    "发票编号", "发票日期", "电话", "传真", "数量"
}

FUZZY_MATCH_FIELDS = {
    "公司名称", "地址", "商品名称及规格型号", "货物名称"
}

NUMBER_MATCH_FIELDS = {
   "货物总数量", "货物总价", "总价", "单价"
}

class FieldItem(BaseModel):
    fieldName: str
    fieldValue: Optional[str] = ""
    index: int
    level: int

class AccuracyRequest(BaseModel):
    standard_fields: List[FieldItem]
    extracted_fields: List[FieldItem]

# 构建字段路径
def build_field_path(all_fields, current_field):
    path = [current_field["fieldName"]]
    parent_index = current_field["index"] - 1

    while parent_index >= 0:
        if parent_index < len(all_fields):
            parent_field = all_fields[parent_index]
            if parent_field["level"] < current_field["level"]:
                if not parent_field.get("fieldValue") or parent_field["fieldValue"].strip() == "":
                    path.insert(0, parent_field["fieldName"])
                    break
        parent_index -= 1

    return " > ".join(path)

# 模糊匹配相似度
def is_similar(a: str, b: str, threshold=0.85) -> bool:
    a = a.strip().replace(" ", "").lower()
    b = b.strip().replace(" ", "").lower()
    return difflib.SequenceMatcher(None, a, b).ratio() >= threshold

# 精确匹配
def is_exact_match(a: str, b: str) -> bool:
    return (a.strip() if a else "") == (b.strip() if b else "")

# 数值匹配
import re

def extract_number(value: str) -> float:
    if not value:
        return 0.0
    match = re.search(r'[-+]?(?:\d+\.\d+|\d+)', value.replace(',', ''))
    return float(match.group()) if match else 0.0

def is_number_match(a: str, b: str) -> bool:
    num_a = extract_number(a)
    num_b = extract_number(b)
    return num_a == num_b

def get_match_type(field_name: str):
    if field_name in EXACT_MATCH_FIELDS:
        return "exact"
    elif field_name in FUZZY_MATCH_FIELDS:
        return "fuzzy"
    else:
        return "exact"  # 默认精确匹配
