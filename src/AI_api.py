from .support_function import GenerateSQLCore, readFile
import torch
import asyncio
from psycopg2 import connect
from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title="API for NL2SQL service")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_name = "Qwen/Qwen2.5-Coder-3B-Instruct"
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
adapter_path = os.path.join(root_path, "save_model/checkpoint-39290")
gen_sql_system = GenerateSQLCore(model_name, adapter_path, device)

print("- Đang mở kết nối đến database...")
conn = connect(
    host="localhost",
    port="5432",
    database="E_commerce",
    user="users_local",
    password="123456",
)
cursor = conn.cursor()
print("=> Mở kết nối đến database thành công !")

print("- Đang lấy schema của database")
schema = readFile(os.path.join(root_path, "src/table_schema.txt"))
print("=> Lấy schema của database thành công")

prompt = "Get all users' information who have ever made a purchase"


class InputText(BaseModel):
    prompt: str


def generate_response(schema, prompt, reAct=3):
    count = 0
    wrong_sql = ""
    results = ""
    while count < reAct:
        try:
            print("- Đang sinh lệnh SQL...")
            sql_answer = gen_sql_system.generate(schema, prompt, wrong_sql)
            # print('=> Lệnh SQL được sinh: ', sql_answer)
            cursor.execute(sql_answer)
            results = cursor.fetchall()
        except:
            count += 1
            wrong_sql = sql_answer
            print(
                f" 🔄️Lệnh SQL không hoạt động ! Tiến hành tạo lại...\nSố lần tạo: {count}/{reAct}"
            )
        else:
            print("✅ Lệnh SQL được tạo thành công !")
            return sql_answer, results
    print("❌ Đã đạt giới hạn số lượt tạo. Trả về lệnh SQL cuối cùng được tạo !")
    return sql_answer, results


@app.post("/generate")
async def generate(request: InputText):
    sql_answer, results = await asyncio.to_thread(
        generate_response, schema, request.prompt
    )
    return {"SQL": sql_answer, "Result": results}


# sql_answer, results = generate_response(schema, prompt)
# print("Lệnh SQL: ", sql_answer)
# print("Kết quả: ", results)
# for row in results:
#     print(row)
