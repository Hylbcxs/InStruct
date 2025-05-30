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


# 导入路由模块
from api.openai_api import router as openai_router
# from api.acc_api import router as acc_router
from api.files.file_router_factory import create_file_router
from api.fields.field_router_factory import create_field_router

load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR")
PORT = int(os.getenv("PORT", "8002"))
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
# 挂载路由
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

@app.get("/api/file/{file_path:path}")
async def get_file(file_path: str):
    print(f"[DEBUG] 请求路径: {file_path}")
    file_location = os.path.join(UPLOAD_DIR, file_path)
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail=f"文件未找到: {file_location}")
    return FileResponse(file_location)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)