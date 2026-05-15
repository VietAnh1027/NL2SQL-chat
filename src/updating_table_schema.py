"""
add_new_schemas_to_vectorstore.py
----------------------------------
Mục đích:
    Đọc các table schema mới từ file "new_table_schema_update.txt",
    dùng LLM (Qwen2.5-Coder-3B-Instruct) sinh metadata cho từng bảng,
    sau đó embed metadata và thêm vào vector store ChromaDB đã tồn tại
    (raw_context = câu lệnh CREATE TABLE gốc).

Cách dùng:
    python add_new_schemas_to_vectorstore.py

Cấu trúc thư mục mặc định (tuỳ chỉnh qua biến Config bên dưới):
    project/
    ├── schema_data/
    │   └── new_table_schema_update.txt   ← input
    ├── vector-store/                     ← ChromaDB persist directory
    └── add_new_schemas_to_vectorstore.py
"""

import os
import re
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma


# ──────────────────────────────────────────────
# CẤU HÌNH – chỉnh sửa các đường dẫn tại đây
# ──────────────────────────────────────────────
class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # File schema mới cần thêm vào vector store
    NEW_SCHEMA_FILE = os.path.join(BASE_DIR, "schema_data", "new_table_schema_update.txt")

    # Thư mục persist của ChromaDB đã tồn tại
    VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector-store")

    # Tên collection trong ChromaDB
    COLLECTION_NAME = "first_collection"

    # Mô hình LLM để sinh metadata
    LLM_MODEL_NAME = "Qwen/Qwen2.5-Coder-3B-Instruct"

    # Mô hình embedding
    EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

    # Số token tối đa sinh ra cho mỗi schema
    MAX_NEW_TOKENS = 512


# ──────────────────────────────────────────────
# SYSTEM PROMPT CHO LLM
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert Database Administrator. Your task is to analyze SQL DDL (CREATE TABLE) and generate JSON metadata to improve Vector Search for a Text-to-SQL RAG system.

STRICT RULES:
1. Output ONLY a valid JSON object. DO NOT wrap the output in markdown code blocks (e.g., no ```json). DO NOT add any conversational text.
2. The JSON must be exactly 1 level deep (FLAT). All values must be STRINGS. No nested objects or arrays.
3. Write "table_description" and "columns_summary" in English.
4. Generate exactly 3 realistic sample data rows respecting the SQL data types.

EXPECTED JSON SCHEMA:
{
"table_name": "<exact_table_name>",
"table_description": "<A detailed description of the function and business logic of this table in English.>",
"columns_summary": "<col1: meaning | col2: meaning | col3: meaning>"
}

EXAMPLE INPUT:
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50),
    is_active BOOLEAN
);

EXAMPLE OUTPUT:
{
"table_name": "users",
"table_description": "Stores user account information in the system, including their unique identifier and active status.",
"columns_summary": "id: unique identifier | username: login name | is_active: account status (true/false)"
}"""


# ──────────────────────────────────────────────
# EMBEDDING WRAPPER (tương thích LangChain)
# ──────────────────────────────────────────────
class EmbeddingModel:
    def __init__(self, model_name: str, device: str):
        print(f"[Embedding] Đang tải model '{model_name}'...")
        self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, data: list[str]) -> list[list[float]]:
        return self.model.encode(data, convert_to_numpy=True).tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.model.encode(query, convert_to_numpy=True).tolist()


# ──────────────────────────────────────────────
# BƯỚC 1: ĐỌC VÀ PARSE TABLE SCHEMA TỪ FILE
# ──────────────────────────────────────────────
def load_schemas(file_path: str) -> list[str]:
    print(f"\n[BƯỚC 1] Đọc schema từ: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    with open(file_path, mode="r", encoding="utf-8") as f:
        raw_text = f.read()

    schema_lst = re.findall(r"CREATE TABLE.*?\);", raw_text, flags=re.DOTALL | re.IGNORECASE)

    if not schema_lst:
        raise ValueError("Không tìm thấy câu lệnh CREATE TABLE nào trong file.")

    print(f"  → Tìm thấy {len(schema_lst)} table schema.")
    return schema_lst


# ──────────────────────────────────────────────
# BƯỚC 2: SINH METADATA BẰNG LLM (BATCH)
# ──────────────────────────────────────────────
def generate_metadata(schema_lst: list[str], config: Config) -> list[str]:
    print(f"\n[BƯỚC 2] Tải LLM '{config.LLM_MODEL_NAME}'...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  → Sử dụng device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(config.LLM_MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(config.LLM_MODEL_NAME)
    model.to(device)
    model.eval()

    # Chuẩn bị tokenizer
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Tạo batch input từ danh sách schema
    print(f"  → Chuẩn bị batch input cho {len(schema_lst)} schema...")
    text_lst = []
    for schema in schema_lst:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": schema},
        ]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        text_lst.append(text)

    model_inputs = tokenizer(
        text_lst,
        padding=True,
        return_tensors="pt",
    ).to(device)

    print(f"  → Đang sinh metadata (max_new_tokens={config.MAX_NEW_TOKENS})...")
    with torch.no_grad():
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=config.MAX_NEW_TOKENS,
            do_sample=False,  # Greedy – kết quả JSON ổn định hơn
        )

    # Cắt bỏ phần prompt, chỉ giữ phần model sinh ra
    trimmed_ids = [
        output[len(inp):]
        for inp, output in zip(model_inputs.input_ids, generated_ids)
    ]
    metadata_lst = tokenizer.batch_decode(trimmed_ids, skip_special_tokens=True)

    # Validate: đảm bảo mỗi output parse được thành JSON
    validated = []
    for i, raw in enumerate(metadata_lst):
        # Trích xuất JSON nếu model vẫn bọc trong code fence
        clean = re.sub(r"```json|```", "", raw).strip()
        try:
            json.loads(clean)   # Kiểm tra tính hợp lệ
            validated.append(clean)
        except json.JSONDecodeError:
            print(f"  [CẢNH BÁO] Schema #{i+1}: output không parse được thành JSON. Giữ nguyên raw output.")
            validated.append(raw.strip())

    print(f"  → Sinh xong metadata cho {len(validated)} table.")
    return validated


# ──────────────────────────────────────────────
# BƯỚC 3: THÊM VÀO VECTOR STORE
# ──────────────────────────────────────────────
def add_to_vector_store(
    schema_lst: list[str],
    metadata_lst: list[str],
    config: Config,
) -> None:
    assert len(schema_lst) == len(metadata_lst), (
        f"Số lượng schema ({len(schema_lst)}) và metadata ({len(metadata_lst)}) không khớp!"
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    embed_model = EmbeddingModel(config.EMBED_MODEL_NAME, device)

    print(f"\n[BƯỚC 3] Kết nối đến vector store tại '{config.VECTOR_STORE_DIR}'...")
    vector_store = Chroma(
        collection_name=config.COLLECTION_NAME,
        persist_directory=config.VECTOR_STORE_DIR,
        embedding_function=embed_model,
        collection_metadata={"hnsw:space": "cosine"},
    )

    # raw_context = câu lệnh CREATE TABLE gốc
    metadatas = [{"raw_context": schema} for schema in schema_lst]

    print(f"  → Đang thêm {len(metadata_lst)} bản ghi vào collection '{config.COLLECTION_NAME}'...")
    vector_store.add_texts(
        texts=metadata_lst,       # Văn bản được embed (metadata JSON)
        metadatas=metadatas,      # Metadata đính kèm (schema gốc)
    )
    print(f"  → Thêm thành công {len(schema_lst)} table schema vào vector store.")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    config = Config()

    print("=" * 60)
    print("  ADD NEW TABLE SCHEMAS TO VECTOR STORE")
    print("=" * 60)

    # Bước 1: Đọc schema
    schema_lst = load_schemas(config.NEW_SCHEMA_FILE)

    # Hiển thị danh sách tên bảng để kiểm tra
    table_names = [
        re.search(r"CREATE TABLE\s+(\w+)", s, re.IGNORECASE).group(1)
        for s in schema_lst
        if re.search(r"CREATE TABLE\s+(\w+)", s, re.IGNORECASE)
    ]
    print(f"  Danh sách bảng: {table_names}")

    # Bước 2: Sinh metadata
    metadata_lst = generate_metadata(schema_lst, config)

    # In preview kết quả
    print("\n  [Preview metadata đã sinh]")
    for i, (schema, meta) in enumerate(zip(schema_lst, metadata_lst)):
        table_match = re.search(r"CREATE TABLE\s+(\w+)", schema, re.IGNORECASE)
        name = table_match.group(1) if table_match else f"table_{i+1}"
        print(f"  Table {i+1}: {name}")
        print(f"    → {meta[:120]}{'...' if len(meta) > 120 else ''}")

    # Bước 3: Thêm vào vector store
    add_to_vector_store(schema_lst, metadata_lst, config)

    print("\n" + "=" * 60)
    print("  HOÀN THÀNH! Tất cả table schema đã được thêm vào vector store.")
    print("=" * 60)


if __name__ == "__main__":
    main()