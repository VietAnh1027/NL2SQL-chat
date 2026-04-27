from .support_function import GenerateSQLCore, readFile
import torch
import asyncio
from psycopg2 import connect
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
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
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "Qwen/Qwen2.5-Coder-3B-Instruct"
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
adapter_path = os.path.join(root_path, "save_model/checkpoint-39290")
gen_sql_system = GenerateSQLCore(model_name, adapter_path, device)

# print("- Đang mở kết nối đến database...")
# conn = connect(
#     host="localhost",
#     port="5432",
#     database=DB_NAME,
#     user=USER,
#     password=PASS
# )
# cursor = conn.cursor()
# print("=> Mở kết nối đến database thành công !")

print("- Đang lấy schema của database")
schema = readFile(os.path.join(root_path, "src/table_schema.txt"))
print("=> Lấy schema của database thành công")

# prompt = "Get all users' information who have ever made a purchase"

def generate_response(schema, prompt, reAct=3):
    count = 0
    wrong_sql = ""
    results = ""
    while count < reAct:
        try:
            print("- Đang sinh lệnh SQL...")
            sql_llm = gen_sql_system.generate(schema, prompt, wrong_sql)
            # print('=> Lệnh SQL được sinh: ', sql_answer)
            sql_answer = sqlglot.transpile(sql_llm, write='postgres')[0]
        except:
            count += 1
            wrong_sql = sql_answer
            print(
                f" 🔄️Lệnh SQL không hoạt động ! Tiến hành tạo lại...\nSố lần tạo: {count}/{reAct}"
            )
        else:
            print("✅ Lệnh SQL được tạo thành công !")
            # # Khi nào query thực tế trong database thì bỏ comment
            # cursor.execute(sql_answer)
            # results = cursor.fetchall()
            return sql_answer, results
    print("❌ Đã đạt giới hạn số lượt tạo. Trả về lệnh SQL cuối cùng được tạo !")
    return "❌ Đã đạt giới hạn số lượt tạo. Trả về lệnh SQL cuối cùng được tạo !\n" + sql_answer, results

class InputText(BaseModel):
    question: str
@app.post("/api/generate-sql")
async def generate(request: InputText):
    sql_answer, results = await asyncio.to_thread(
        generate_response, schema, request.question
    )
    return {"sql_query": sql_answer, "results": results}


# sql_answer, results = generate_response(schema, prompt)
# print("Lệnh SQL: ", sql_answer)
# print("Kết quả: ", results)
# for row in results:
#     print(row)
