from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from utils.acc_utils import (
    FieldItem,
    AccuracyRequest,
    build_field_path,
    get_match_type,
    is_exact_match,
    is_similar,
    is_number_match
)

router = APIRouter(prefix="/api")
@router.post("/calculate-accuracy")
async def calculate_accuracy(request: AccuracyRequest):
    standard_fields = [dict(f) for f in request.standard_fields]
    extracted_fields = [dict(f) for f in request.extracted_fields]

    # 构建标准字段路径映射
    standard_map = {}
    for field in standard_fields:
        path = build_field_path(standard_fields, field)
        standard_map[path] = field

    print(standard_map)

    match_count = 0
    total_count = 0
    details = []

    for field in extracted_fields:
        path = build_field_path(extracted_fields, field)
        standard_field = standard_map.get(path)

        if not standard_field:
            continue  # 跳过不在标准字段中的多余字段

        extracted_value = (field.get("fieldValue") or "").strip()
        standard_value = (standard_field.get("fieldValue") or "").strip()

        field_name = field["fieldName"]
        match_type = get_match_type(field_name)

        matched = False
        if match_type == "exact":
            matched = is_exact_match(extracted_value, standard_value)
        elif match_type == "fuzzy":
            matched = is_similar(extracted_value, standard_value)
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
    print(details)

    accuracy_rate = round((match_count / total_count * 100), 2) if total_count > 0 else 0

    return JSONResponse(content={
        "matchCount": match_count,
        "totalCount": total_count,
        "accuracyRate": accuracy_rate,
        "details": details
    })