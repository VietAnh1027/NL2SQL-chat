from transformers import AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer
from peft import PeftModel
import torch

class EmbeddingModel:
    def __init__(self, model, device):
        self.model = SentenceTransformer(model, device=device)

    def embed_documents(self,data):
        return self.model.encode_document(data)

    def embed_query(self, query):
        return self.model.encode_query(query)

class GenerateSQLCore:
    def __init__(self, model_name, adapter_path, device):
        base_model = AutoModelForCausalLM.from_pretrained(
            model_name, dtype=torch.bfloat16, device_map=device
        )
        self.device = device
        self.model = PeftModel.from_pretrained(base_model, adapter_path)
        # self.model = base_model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model.eval()

    def generate(self, schema, query, wrong_sql="", error_msg="", debug=False):
        messages = [
            {
                "role": "system",
                "content": f"""You are a highly specialized NL2SQL engine. Your ONLY task is to translate natural language into accurate SQL queries based on the provided schema.

CRITICAL RULES:
1. Output EXACTLY ONE valid SQL query.
2. DO NOT include any greetings, explanations, or conversational text before or after the query.
3. DO NOT wrap the SQL query in markdown formatting blocks (e.g., strictly NO ```sql or ``` tags). Return raw text only.

Schema: \n{schema}""",
            }
        ]

        if wrong_sql and error_msg:
            user_prompt = (
                """CRITICAL RULES:
1. Output EXACTLY ONE valid SQL query.
2. DO NOT include any greetings, explanations, or conversational text before or after the query.
3. DO NOT wrap the SQL query in markdown formatting blocks (e.g., strictly NO ```sql or ``` tags). Return raw text only."""
                f"Question: {query}\n\n"
                f"You previously generated the following SQL which caused an error:\n{wrong_sql}\n\n"
                f"Error Message from Database/Parser:\n{error_msg}\n\n"
                f"Please fix the SQL query to resolve this exact error."
            )
        else:
            user_prompt = query

        messages.append({"role": "user", "content": user_prompt})

        input_text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        with torch.no_grad():
            tokens = self.tokenizer(input_text, return_tensors="pt").to(self.device)

            prompt_length = tokens["input_ids"].shape[1]

            output = self.model.generate(
                **tokens, max_new_tokens=512, pad_token_id=self.tokenizer.eos_token_id
            )

            if not debug:
                final_tokens = output[0][prompt_length:]
            else:
                final_tokens = output[0]
            response = self.tokenizer.decode(final_tokens, skip_special_tokens=True)
            return response.strip()

def get_schema_based_query(vector_store, query, topK):
    if topK == 0: topK = 5
    schema_filtered = ""
    rag_answer = vector_store.similarity_search(query, k=topK)
    print("=== RAG ANSWER ===\n")
    for doc in rag_answer:
        print(doc.metadata.get("raw_context"))
        schema_filtered += doc.metadata.get("raw_context") + '\n'
    return schema_filtered