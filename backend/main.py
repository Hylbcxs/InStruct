import os
import base64
import json
import asyncio
import shutil
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse

from openai import OpenAI

from database.database import init_db
from models.file_models import InvoiceModel, DeclarationModel, ContractModel, LandingModel

# from acc_utils import (
#     FieldItem,
#     AccuracyRequest,
#     build_field_path,
#     get_match_type,
#     is_exact_match,
#     is_similar,
#     is_number_match
# )

# 导入路由模块
# from api.files.invoice_files_api import router as files_router
# from api.fields.invoice_fields_api import router as fields_router
from api.openai_api import router as openai_router
from api.acc_api import router as acc_router
from api.files.file_router_factory import create_file_router
from api.fields.field_router_factory import create_field_router

load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR")
# 定义 lifespan 函数
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("⏳ 初始化数据库...")
    init_db()
    print("✅ 数据库初始化完成")
    
    yield  # 应用运行期间
    
    # Shutdown（可选）
    print("🔌 关闭数据库连接...")

# 创建 FastAPI 实例并传入 lifespan
app = FastAPI(lifespan=lifespan)
# invoice_router = create_file_router(InvoiceModel, file_prefix="/发票", url_prefix="/invoice")
# declaration_router = create_file_router(DeclarationModel, file_prefix="/报关单", url_prefix="/declaration")
# contract_router = create_file_router(ContractModel, file_prefix="/合同", url_prefix="/contract")
# landing_router = create_file_router(LandingModel, file_prefix="/提单", url_prefix="/landing")

# # 挂载路由

# # app.include_router(files_router)
# app.include_router(invoice_router)
# app.include_router(invoice_router)
# app.include_router(declaration_router)
# app.include_router(landing_router)
# 为每个模型生成 file 和 field 路由，并注册到 app
models_config = [
    {
        "model": InvoiceModel,
        "file_prefix": "/发票",
        "field_prefix": "/invoice",
    },
    {
        "model": DeclarationModel,
        "file_prefix": "/报关单",
        "field_prefix": "/declaration",
    },
    {
        "model": ContractModel,
        "file_prefix": "/合同",
        "field_prefix": "/contract",
    },
    {
        "model": LandingModel,
        "file_prefix": "/提单",
        "field_prefix": "/landing",
    },
]

for config in models_config:
    model_class = config["model"]
    file_router = create_file_router(model_class, file_prefix=config["file_prefix"], url_prefix=f"{config['field_prefix']}")
    field_router = create_field_router(model_class, url_prefix=f"{config['field_prefix']}")

    app.include_router(file_router)
    app.include_router(field_router)

app.include_router(openai_router)

# app.include_router(fields_router)
# app.include_router(acc_router)
# app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
# 挂载打包好的前端
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("../frontend/index.html")


# @app.post("/api/extract")
# async def extract_fields(payload: dict):
#     prompt = """
#     请分析图片内容，并提取其中包含的所有字段及对应的值，以 JSON 格式输出。
#     要求如下：
#     1. 每个字段作为 JSON 的一个键；
#     2. 每个字段的值为图片中对应的语义内容；
#     3. 如果某个字段包含子项，请使用嵌套的 JSON 结构展示；
#     4. 不需要包含位置信息、类型或其他元数据；
#     5. 注意：请只输出 JSON，不要添加任何解释或文本说明，也不要使用 Markdown 包裹！格式示例：
#     {
#     "姓名": "张三",
#     "性别": "男",
#     "学历信息": {
#         "学校": "清华大学",
#         "专业": "计算机科学",
#         "学历": "本科"
#     },
#     "工作经历": {
#         "公司": "字节跳动",
#         "职位": "前端工程师"
#     }
#     }
#     请确保字段尽可能完整、语义准确，保持 JSON 结构规范。
#     """
#     image_url = payload.get("image_url", "")
#     InvoicePrompt = payload.get("prompt", prompt)

#     if not image_url:
#         raise HTTPException(status_code=400, detail="缺少图片路径")

#     # 构造完整路径（假设图片放在 public 下）
#     full_path = os.path.join("../frontend/public", image_url.lstrip("/"))

#     if not os.path.exists(full_path):
#         raise HTTPException(status_code=400, detail="图片不存在")

#     # 调用模型
    
#     try:
#         response = client.chat.completions.create(
#             model='Qwen/Qwen2.5-VL-32B-Instruct',
#             # model='Qwen/Qwen2.5-VL-72B-Instruct',
#             messages=[{
#                 'role': 'user',
#                 'content': [
#                     {'type': 'text', 'text': InvoicePrompt},
#                     {'type': 'image_url', 'image_url': {
#                         'url': f"data:image/jpeg;base64,{image_to_base64(full_path)}"
#                     }},
#                 ]
#             }],
#             stream=True
#         )

#         # 流式返回结果
#         async def fake_json_streamer():
#             for chunk in response:
#                 content = chunk.choices[0].delta.content
#                 if content:
#                     yield content  # 逐块发送给前端

    
#         return StreamingResponse(fake_json_streamer(), media_type="application/json")

#     except Exception as e:
#         print("Error during model call:", str(e))  # 添加这行
#         raise HTTPException(status_code=500, detail=str(e))

# 上传图片文件
@app.post("/api/upload")
def upload_file(
    file: UploadFile = File(...),
    uploadDir: str = Form(...)
):
    # 确保目标目录存在
    os.makedirs(uploadDir, exist_ok=True)

    # 构造目标文件路径
    file_location = os.path.join(uploadDir, file.filename)

    # 写入文件
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return Response(
        content=json.dumps({"filename": file.filename}).encode('utf-8'),
        media_type="application/json",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# 删除图片文件
@app.post("/api/delete-file")
def delete_file(
    filename: str = Form(...),
    uploadDir: str = Form(...)
):
    file_path = os.path.join(uploadDir, filename)

    if not os.path.exists(file_path):
        return {"success": False, "message": "文件不存在"}

    try:
        os.remove(file_path)
        return {"success": True, "message": f"文件 {filename} 已删除"}
    except Exception as e:
        return {"success": False, "message": f"删除失败: {str(e)}"}
    
@app.post("/api/clear-files")
def clear_files(payload: dict):
    upload_dir = payload.get("uploadDir", "")
    if not os.path.exists(upload_dir):
        return {"success": False, "message": "目录不存在"}

    try:
        # 遍历并删除所有文件
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            os.remove(file_path)

        return {"success": True, "message": f"{upload_dir} 下所有文件已清空"}
    except Exception as e:
        return {"success": False, "message": f"清空失败: {str(e)}"}

# 禁用缓存
# @app.get("/发票/{filename:path}")
# async def read_invoice(filename: str):
#     print("读取这个")
#     file_path = f"public/发票/{filename}"
#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="File not found")
#     return FileResponse(
#         file_path,
#         headers={
#             "Cache-Control": "no-cache, no-store, must-revalidate",
#             "Pragma": "no-cache",
#             "Expires": "0"
#         }
#     )
@app.get("/api/file/{file_path:path}")
async def get_file(file_path: str):
    print(f"[DEBUG] 请求路径: {file_path}")
    file_location = os.path.join(UPLOAD_DIR, file_path)
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail=f"文件未找到: {file_location}")
    return FileResponse(file_location)

# 路由：计算准确率
# @app.post("/api/calculate-accuracy")
# async def calculate_accuracy(request: AccuracyRequest):
#     standard_fields = [dict(f) for f in request.standard_fields]
#     extracted_fields = [dict(f) for f in request.extracted_fields]

#     # 构建标准字段路径映射
#     standard_map = {}
#     for field in standard_fields:
#         path = build_field_path(standard_fields, field)
#         standard_map[path] = field

#     print(standard_map)

#     match_count = 0
#     total_count = 0
#     details = []

#     for field in extracted_fields:
#         path = build_field_path(extracted_fields, field)
#         standard_field = standard_map.get(path)

#         if not standard_field:
#             continue  # 跳过不在标准字段中的多余字段

#         extracted_value = (field.get("fieldValue") or "").strip()
#         standard_value = (standard_field.get("fieldValue") or "").strip()

#         field_name = field["fieldName"]
#         match_type = get_match_type(field_name)

#         matched = False
#         if match_type == "exact":
#             matched = is_exact_match(extracted_value, standard_value)
#         elif match_type == "fuzzy":
#             matched = is_similar(extracted_value, standard_value)
#         elif match_type == "number":
#             matched = is_number_match(extracted_value, standard_value)

#         if matched:
#             match_count += 1

#         total_count += 1
#         details.append({
#             "path": path,
#             "standardValue": standard_value,
#             "extractedValue": extracted_value,
#             "matched": matched
#         })
#     print(details)

#     accuracy_rate = round((match_count / total_count * 100), 2) if total_count > 0 else 0

#     return JSONResponse(content={
#         "matchCount": match_count,
#         "totalCount": total_count,
#         "accuracyRate": accuracy_rate,
#         "details": details
#     })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)