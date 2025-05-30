#!/bin/bash

# 设置标准字段和提取结果的 JSON 文件路径
STANDARD_JSON="/opt/data/private/hyl/code/InStruct/frontend/public/standard/报关单/报关单2.json"
EXTRACTED_JSON="/opt/data/private/hyl/code/InStruct/backend/output/报关单/报关单2_useocr_False.json"
OUTPUT_JSON="/opt/data/private/hyl/code/InStruct/backend/utils/accuracy_result.json"
NAME="报关单2_useocr_False"

# 执行 Python 脚本
python /opt/data/private/hyl/code/InStruct/backend/utils/acc_utils.py \
  --standard "$STANDARD_JSON" \
  --extracted "$EXTRACTED_JSON" \
  --output "$OUTPUT_JSON" \
  --name "$NAME"

# 检查是否执行成功
if [ $? -eq 0 ]; then
  echo "✅ 准确率计算完成，结果已保存到 $OUTPUT_JSON"
else
  echo "❌ 准确率计算失败"
fi