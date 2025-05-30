import json
import difflib
import re
import os
import argparse

# 匹配规则配置
EXACT_MATCH_FIELDS = {
    "发票编号", "发票日期", "电话", "传真", "数量"
}

FUZZY_MATCH_FIELDS = {
    "公司名称", "地址", "货物名称", "货物名称及规格型号"
}

NUMBER_MATCH_FIELDS = {
   
}


def flatten_json(data, prefix=""):
    """
    递归扁平化 JSON，生成字段路径和值的映射
    例如：
        {'卖方信息': {'公司名称': 'xxx'}} => {'卖方信息 > 公司名称': 'xxx'}
    """
    result = {}

    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix} > {key}" if prefix else key
            sub_flat = flatten_json(value, new_prefix)
            result.update(sub_flat)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_prefix = f"{prefix}[{i}]"
            sub_flat = flatten_json(item, new_prefix)
            result.update(sub_flat)
    else:
        result[prefix] = data

    return result


def is_similar(a: str, b: str, threshold=0.85) -> bool:
    a = a.strip().replace(" ", "").lower()
    b = b.strip().replace(" ", "").lower()
    return difflib.SequenceMatcher(None, a, b).ratio() >= threshold


def is_exact_match(a, b):
    return str(a).strip() == str(b).strip()


def extract_number(value):
    if not value:
        return 0.0
    match = re.search(r'[-+]?(?:\d+\.\d+|\d+)', str(value).replace(',', ''))
    return float(match.group()) if match else 0.0


def is_number_match(a, b):
    num_a = extract_number(a)
    num_b = extract_number(b)
    return num_a == num_b


def get_match_type(field_name):
    if field_name in EXACT_MATCH_FIELDS:
        return "exact"
    elif field_name in FUZZY_MATCH_FIELDS:
        return "fuzzy"
    elif field_name in NUMBER_MATCH_FIELDS:
        return "number"
    else:
        return "exact"  # 默认精确匹配


def calculate_accuracy(standard_json, extracted_json, name):
    # 扁平化两个 JSON
    standard_flat = flatten_json(standard_json)
    extracted_flat = flatten_json(extracted_json)

    match_count = 0
    total_count = 0
    details = []

    for path, standard_value in standard_flat.items():
        extracted_value = extracted_flat.get(path)

        # 提取字段名（最后一层路径）
        field_name = path.split(" > ")[-1].split("[")[0]

        # 判断是否在提取结果中存在
        if path not in extracted_flat:
            details.append({
                "path": path,
                "standardValue": standard_value,
                "extractedValue": None,
                "matched": False
            })
            total_count += 1
            continue

        match_type = get_match_type(field_name)

        matched = False
        if match_type == "exact":
            matched = is_exact_match(extracted_value, standard_value)
        elif match_type == "fuzzy":
            matched = is_similar(str(extracted_value), str(standard_value))
        elif match_type == "number":
            matched = is_number_match(extracted_value, standard_value)

        if matched:
            match_count += 1

        total_count += 1
        details.append({
            "path": path,
            "standardValue": standard_value,
            "extractedValue": extracted_value,
            "matched": matched
        })

    accuracy_rate = round((match_count / total_count * 100), 2) if total_count > 0 else 0

    return {
        "name": name,
        "matchCount": match_count,
        "totalCount": total_count,
        "accuracyRate": accuracy_rate,
        "details": details
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="比较两个嵌套 JSON 文件的字段提取准确率")
    parser.add_argument("--standard", "-s", type=str, required=True, help="标准字段 JSON 文件路径")
    parser.add_argument("--extracted", "-e", type=str, required=True, help="模型提取结果 JSON 文件路径")
    parser.add_argument("--name", "-n", type=str, required=True, help="模型提取结果 JSON 文件路径")
    parser.add_argument("--output", "-o", type=str, default=None, help="输出结果 JSON 文件路径（可选）")

    args = parser.parse_args()

    with open(args.standard, "r", encoding="utf-8") as f:
        standard_data = json.load(f)

    with open(args.extracted, "r", encoding="utf-8") as f:
        extracted_data = json.load(f)

    result = calculate_accuracy(standard_data, extracted_data, args.name)

    print("\n📊 准确率统计：")
    print(f"匹配字段数：{result['matchCount']}/{result['totalCount']}")
    print(f"准确率：{result['accuracyRate']}%")

    print("\n📋 匹配详情：")
    for detail in result["details"]:
        status = "✅ 匹配成功" if detail["matched"] else "❌ 不匹配"
        print(
            f"{detail['path']} | 标准值: {detail['standardValue']} | 提取值: {detail['extractedValue']} | 状态: {status}")

    # 读取已有内容（如果存在）
    existing_data = []
    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                # 如果文件为空或格式错误，则从空列表开始
                existing_data = []

    # 添加新结果
    existing_data.append(result)

    # 写回文件（仍然是 "w" 模式，但内容包含之前的结果）
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ 结果已保存到：{args.output}")