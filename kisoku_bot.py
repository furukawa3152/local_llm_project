import streamlit as st
import ollama
import os

st.set_page_config(page_title="就業規則 Bot", layout="wide")

st.title("📜 就業規則 FAQ Bot")

# **就業規則データを読み込む関数（TXT のみ）**
def load_regulations(file_path):
    if file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "対応していないファイル形式です"

# **就業規則のTXTファイルを指定**
REGULATIONS_FILE = "shugyokisoku.txt"  # 就業規則のテキストファイル
if not os.path.exists(REGULATIONS_FILE):
    st.error("⚠ 就業規則のTXTファイルが見つかりません！")
    st.stop()

# **就業規則のデータをロード**
regulations_text = load_regulations(REGULATIONS_FILE)

# **質問処理**
user_question = st.chat_input("就業規則について質問してください...")
if user_question:
    # **Ollama に文脈付きで質問を送信**
    response = ollama.chat(
        model="Gemma3:latest",
        messages=[
            {"role": "system", "content": "以下の就業規則に基づいて質問に答えてください。\n\n" + regulations_text},
            {"role": "user", "content": user_question},
        ]
    )

    bot_answer = response["message"]["content"]

    # **回答の表示**
    with st.chat_message("user"):
        st.markdown(user_question)
    with st.chat_message("assistant"):
        st.markdown(bot_answer)
