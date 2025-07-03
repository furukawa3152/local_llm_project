from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import ollama
from md2text import markdown_to_plain_text
import json
import csv
import re
from datetime import datetime
import time
from make_spleted_summary import make_spleted_summary, split_text_by_words, MODEL_NAME,split_text_by_week
from gairai_text_fetch import fetch_and_print_text_file_by_id,extract_ascending_soap_text
from houmonkango_text_convert import process_text,wareki_split_text_by_words,make_spleted_houkansummary
app = FastAPI()
#MODEL_NAME = "Llama-Gemma-2-27b-ORPO-iter3.Q8_0.gguf:latest"
#MODEL_NAME = "Llama-Gemma-2-27b-ORPO-iter3.Q6_K.gguf:latest"
MODEL_NAME = "Gemma3:27b"
lock = asyncio.Lock()

CSV_FILE = "chat_history.csv"

#サーバ起動コマンド　uvicorn gemma_API:app --host 0.0.0.0 --port 8101


class QuestionRequest(BaseModel):
    question: str
    prompt: str = "hello"
    max_tokens: int = 8000

class gairaiRequest(BaseModel):
    ptid: str
    prompt: str = "hello"
    max_tokens: int = 8000

async def ask_model(question: str, max_tokens: int) -> dict:
    start_time = time.time()  # 処理開始時間を記録
    async with lock:
        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=[
                    {'role': 'system',
                     'content': 'あなたは優秀な日本語のアシスタントです。指示に忠実に回答してください。'},
                    {"role": "user", "content": question}
                ],
                #options={"num_predict": max_tokens, "temperature": 0.1}
                options = {"temperature": 0}
            )
            answer = response["message"]["content"]
            print(answer)
            no_md_answer = markdown_to_plain_text(response["message"]["content"])
            end_time = time.time()  # 処理終了時間
            elapsed_time = round(end_time - start_time, 3)  # 経過時間（秒）

            # 文字数計算
            input_length = len(question)
            output_length = len(no_md_answer)

            log_to_csv(question, no_md_answer)  # CSVに記録

            return {
                "answer": no_md_answer,
                "input_length": input_length,
                "output_length": output_length,
                "elapsed_time": elapsed_time
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

async def ask_model_12b(question: str, max_tokens: int) -> dict:
    start_time = time.time()  # 処理開始時間を記録
    async with lock:
        try:
            response = ollama.chat(
                model="Gemma3:12b",
                messages=[
                    {'role': 'system',
                     'content': 'あなたは優秀な日本語のアシスタントです。指示に忠実に回答してください。'},
                    {"role": "user", "content": question}
                ],
                #options={"num_predict": max_tokens, "temperature": 0.1}
                options = {"temperature": 0}
            )
            answer = response["message"]["content"]
            print(answer)
            no_md_answer = markdown_to_plain_text(response["message"]["content"])
            end_time = time.time()  # 処理終了時間
            elapsed_time = round(end_time - start_time, 3)  # 経過時間（秒）

            # 文字数計算
            input_length = len(question)
            output_length = len(no_md_answer)

            log_to_csv(question, no_md_answer)  # CSVに記録

            return {
                "answer": no_md_answer,
                "input_length": input_length,
                "output_length": output_length,
                "elapsed_time": elapsed_time
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
async def model_houmonkango(question: str, prompt: str) -> dict:
    model = "Gemma3:12b"
    start_time = time.time()  # 処理開始時間を記録
    #不要文字列削除、年付き表示を整理する。
    processed_text = process_text(question)
    print(processed_text)
    split_text = wareki_split_text_by_words(processed_text, max_words=2000)
    first_summarised_text = make_spleted_houkansummary(split_text)
    print(first_summarised_text)
    async with lock:
        try:
            response = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system',
                     'content': f'あなたは優秀な日本語のアシスタントです。{prompt}'},
                    {"role": "user", "content": first_summarised_text} #first_summarised_text から一時的に変更
                ],
                #options={"num_predict": max_tokens, "temperature": 0.1}
                options = {"temperature": 0}
            )
            answer = response["message"]["content"]
            print(answer)
            no_md_answer = markdown_to_plain_text(response["message"]["content"])
            end_time = time.time()  # 処理終了時間
            elapsed_time = round(end_time - start_time, 3)  # 経過時間（秒）

            # 文字数計算
            input_length = len(question)
            output_length = len(no_md_answer)

            log_to_csv(question, no_md_answer)  # CSVに記録

            return {
                "answer": no_md_answer,
                "input_length": input_length,
                "output_length": output_length,
                "elapsed_time": elapsed_time,
                "model_name" : model
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
async def summary_model(question: str, prompt: str) -> dict:
    start_time = time.time()  # 処理開始時間を記録
    #split_text = split_text_by_words(question, max_words=1000)
    split_text = split_text_by_week(question)
    first_summarised_text = make_spleted_summary(split_text)
    print(first_summarised_text)
    async with lock:
        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=[
                    {'role': 'system',
                     'content': f'あなたは優秀な日本語のアシスタントです。{prompt}'},
                    {"role": "user", "content": first_summarised_text} #first_summarised_text から一時的に変更
                ],
                #options={"num_predict": max_tokens, "temperature": 0.1}
                options = {"temperature": 0}
            )
            answer = response["message"]["content"]
            print(answer)
            no_md_answer = markdown_to_plain_text(response["message"]["content"])
            end_time = time.time()  # 処理終了時間
            elapsed_time = round(end_time - start_time, 3)  # 経過時間（秒）

            # 文字数計算
            input_length = len(question)
            output_length = len(no_md_answer)

            log_to_csv(question, no_md_answer)  # CSVに記録

            return {
                "answer": no_md_answer,
                "input_length": input_length,
                "output_length": output_length,
                "elapsed_time": elapsed_time,
                "model_name" : MODEL_NAME
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

async def gairai_summary_model(ptid: str, prompt: str) -> dict:
    start_time = time.time()  # 処理開始時間を記録
    model_name = "Gemma3:12b"
    #model_name = "qwen3:14b"
    #model_name = "qwen3:4b"
    #model_name = "qwen3:32b"
    #split_text = split_text_by_words(question, max_words=1000)
    text = fetch_and_print_text_file_by_id(int(ptid))
    shorted_text = extract_ascending_soap_text(text, max_chars=2000)
    print(shorted_text)
    async with lock:
        try:
            response = ollama.chat(
                model= model_name,
                messages=[
                    {'role': 'system',
                     'content': f'あなたは優秀な日本語のアシスタントです。{prompt}'},
                    {"role": "user", "content": shorted_text}
                ],
                #options={"num_predict": max_tokens, "temperature": 0.1}
                options = {"temperature": 0 ,'enable_thinking': True}
            )
            answer = response["message"]["content"]
            no_md_answer = markdown_to_plain_text(answer)
            if len(text) != len(shorted_text):
                no_md_answer = "受診歴が長期のため、直近の内容のみを要約しています。" + "\n" + no_md_answer
            end_time = time.time()  # 処理終了時間
            elapsed_time = round(end_time - start_time, 3)  # 経過時間（秒）

            # 文字数計算
            input_length = len(shorted_text)
            output_length = len(no_md_answer)

            log_to_csv(text, no_md_answer)  # CSVに記録

            return {
                "answer": no_md_answer,
                "input_length": input_length,
                "output_length": output_length,
                "elapsed_time": elapsed_time,
                "model_name" : model_name
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


async def chat_model(message_list: list, max_tokens: int) -> str:
    async with lock:
        try:
            response = ollama.chat(
                model="Gemma3:latest",
                messages=message_list,
                options={"num_predict": max_tokens, "temperature": 0.1}
            )
            answer = markdown_to_plain_text(response["message"]["content"])
            log_to_csv(json.dumps(message_list, ensure_ascii=False), answer)  # CSVに記録
            return answer
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


def log_to_csv(question: str, answer: str):
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().isoformat(), question, answer])


async def ask_hitoiki(question: str) -> str:
    async with lock:
        try:
            response = ollama.chat(
                model="qwen3:4b",
                messages=[
                    {'role': 'system',
                     'content': '''あなたは、過酷な現場で働く医療従事者の心を癒す、温かく思いやりのあるAIアシスタントです
                     質問に対して、親しみがあり、共感的で、前向きな一言添えを含む一問一答形式で答えてください。冗長な会話形式は使わず、その質問に対する1つの完結した回答だけを返してください。
                     **禁止事項**チャット形式の応答や、次の質問を促す言葉（例：他に聞きたいことは？）は一切含めないでください。
                     言葉づかいは、軽快で友人のような口調で、小さな努力を讃えたり、『お疲れ様』などの励ましの言葉を自然に織り交ぜてください。'''},
                    {"role": "user", "content": question}
                ],
                #options={"num_predict": max_tokens, "temperature": 0.1}
                options = {"temperature": 0.5}
            )
            answer = response["message"]["content"]
            print(answer)
            no_md_answer = markdown_to_plain_text(response["message"]["content"])

            log_to_csv(question, no_md_answer)  # CSVに記録

            return no_md_answer
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask(request: QuestionRequest):
    response_data = await ask_model(request.question, request.max_tokens)
    return {
        "answer": f"POSTされた文字数：{response_data['input_length']}文字、返した文字数：{response_data['output_length']}文字、処理にかかった時間：{response_data['elapsed_time']}秒" + "\n" + response_data["answer"],
    }


@app.post("/chat")
async def chat(request: QuestionRequest):
    post_text = request.question.replace("'", '"')
    response = await chat_model(json.loads(post_text), request.max_tokens)
    return {"answer": response}
summary_lock = asyncio.Lock()  # 重い処理用のロック
@app.post("/summary")
async def summarise(request: QuestionRequest):
    async with summary_lock:  # summary_modelはこれで排他
        response_data = await summary_model(request.question, request.prompt)
    return {
        "answer": f"model:{response_data['model_name']},POSTされた文字数：{response_data['input_length']}文字、返した文字数：{response_data['output_length']}文字、処理にかかった時間：{response_data['elapsed_time']}秒" + "\n" + response_data["answer"],
    }

@app.post("/gairai_summary")
async def gairai_summarise(request: gairaiRequest):
    async with summary_lock:  # summary_modelと排他で動く
        # 仮に別の重い関数を使う場合でも排他される
        response_data = await gairai_summary_model(request.ptid, request.prompt)
    return {
        "answer": f"[ALT] model:{response_data['model_name']}、POST:{response_data['input_length']}文字、返答:{response_data['output_length']}文字、時間:{response_data['elapsed_time']}秒\n" + response_data["answer"],
    }

@app.post("/for_hitoiki")
async def for_hitoiki(request: QuestionRequest):
    response_data = await ask_hitoiki(request.question)
    return {
        "answer": response_data
    }

@app.post("/houkan")
async def summarise_houmon(request: QuestionRequest):
    response_data = await model_houmonkango(request.question, request.prompt)
    return {
        "answer": f"model:{response_data['model_name']},POSTされた文字数：{response_data['input_length']}文字、返した文字数：{response_data['output_length']}文字、処理にかかった時間：{response_data['elapsed_time']}秒" + "\n" + response_data["answer"],
    }

@app.post("/ask12b")
async def ask12b(request: QuestionRequest):
    response_data = await ask_model_12b(request.question, request.max_tokens)
    return {
        "answer": f"POSTされた文字数：{response_data['input_length']}文字、返した文字数：{response_data['output_length']}文字、処理にかかった時間：{response_data['elapsed_time']}秒" + "\n" + response_data["answer"],
    }