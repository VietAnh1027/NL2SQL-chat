from .support_function import GenerateSQLCore, get_schema_based_query, EmbeddingModel
from langchain_chroma import Chroma
import torch
import asyncio
from psycopg2 import connect
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re
from dotenv import load_dotenv
import sqlglot

# Khai báo biến môi trường
load_dotenv()
DB_NAME = os.getenv("DB_NAME")
USER = os.getenv("USER")
PASS = os.getenv("PASSWORD")

app = FastAPI(title="API for NL2SQL service")
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8080"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# Khai báo các path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
adapter_path = os.path.join(root_path, "save_model/best-checkpoint-39290")
vector_path = os.path.join(root_path, "vector-store")

# Khai báo LLM model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "Qwen/Qwen2.5-Coder-3B-Instruct"
gen_sql_system = GenerateSQLCore(model_name, adapter_path, device)

# Khai báo Embedding model
embed_name = EmbeddingModel("all-MiniLM-L6-v2", device)

# Khai báo vector store
vector_store = Chroma(
    collection_name="first_collection",
    persist_directory=vector_path,
    embedding_function=embed_name,
    collection_metadata={"hnsw:space": "cosine"}
)

print("- Đang mở kết nối đến database nghiệp vụ...")
conn = connect(
    host="localhost",
    port="5432",
    database=DB_NAME,
    user=USER,
    password=PASS
)
cursor = conn.cursor()
print("=> Mở kết nối đến database nghiệp vụ thành công !")

def generate_response(query, topK, reAct=4):
    count = 0
    sql_answer = ""
    wrong_sql = ""
    error_msg = ""
    results = ""
    forbidden_pattern = r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|REPLACE|EXECUTE)\b'

    print("- Đang trích xuất schema...")
    
    while count < reAct:
        try:
            filtered_schema = get_schema_based_query(vector_store, query, topK + count)
            print("- Đang sinh lệnh SQL...")
            sql_llm = gen_sql_system.generate(filtered_schema, query, wrong_sql, error_msg)
            wrong_sql = sql_llm

            if re.search(forbidden_pattern, sql_llm, re.IGNORECASE):
                print("🚨 CẢNH BÁO BẢO MẬT: Phát hiện từ khóa thay đổi dữ liệu/cấu trúc.")
                return "🚨 Phát hiện từ khóa thay đổi dữ liệu/cấu trúc. Quyền thực thi vào database bị từ chối", results

            sql_answer = sqlglot.transpile(sql_llm, write='postgres')[0]
            cursor.execute(sql_answer)
            print("✅ Lệnh SQL được tạo và thực thi thành công !")
            results = cursor.fetchall()
            return sql_answer, results

        except Exception as e:
            if cursor.connection:
                    cursor.connection.rollback()
            error_msg = str(e)
            if "permission denied" in error_msg.lower():
                print(f"🚨 CẢNH BÁO BẢO MẬT: Database từ chối quyền thực thi. Chi tiết: {error_msg}")
                return "🚨 Phát hiện từ khóa thay đổi dữ liệu/cấu trúc. Quyền thực thi vào database bị từ chối", results
            count += 1
            print(f" 🔄 Lệnh SQL lỗi! Chi tiết: {error_msg}")
            print(f"    Tiến hành tạo lại... Số lần tạo: {count}/{reAct}")
            
    print("❌ Đã đạt giới hạn số lượt tạo")
    error_report = f"❌ Đã đạt giới hạn số lượt tạo.\nSQL cuối cùng: {wrong_sql}\nLỗi hệ thống: {error_msg}"
    return error_report, results

class InputText(BaseModel):
    question: str
    topK: int
@app.post("/api/generate-sql")
async def generate(request: InputText):
    sql_answer, results = await asyncio.to_thread(
        generate_response, request.question, request.topK
    )
    return {"sql_query": sql_answer, "results": results}