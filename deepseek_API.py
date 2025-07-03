import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
from md2text import markdown_to_plain_text

# FastAPI インスタンス作成
app = FastAPI()

# モデル名（Ollamaで使用するモデル）
#MODEL_NAME = "hf.co/mmnga/cyberagent-DeepSeek-R1-Distill-Qwen-14B-Japanese-gguf"
MODEL_NAME="qwq:32b"
# リクエストデータのモデル
class QuestionRequest(BaseModel):
    question: str
    max_tokens: int = 8000  # デフォルトの最大トークン数

async def ask_model(question: str, max_tokens: int) -> str:
    """
    Ollamaを使用してユーザーの質問に対する回答を生成する。
    """
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system','content': 'あなたは優秀な日本語のアシスタントです。論理的かつ簡潔に回答してください。'},
                {"role": "user", "content": question}
            ],
            options={"num_predict": max_tokens,"temperature" :0.1,}
        )
        md_converted_text = markdown_to_plain_text(response["message"]["content"])
        return md_converted_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask(request: QuestionRequest):
    """
    ユーザーからの質問を処理し、Ollamaの応答を返す。
    """
    response = await ask_model(request.question, request.max_tokens)
    return {"answer": response}