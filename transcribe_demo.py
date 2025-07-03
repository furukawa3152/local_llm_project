import streamlit as st
import subprocess
import tempfile
import os
import ollama

MODEL_NAME = "Gemma3:4b"
def summarize_text(edited_text):
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {'role': 'system',
             'content': f'あなたは優秀な翻訳家です。以下に与える文章を日本語に訳してください。**出力は必ず日本語で行うこと。**'},
            {"role": "user", "content": edited_text}
        ],
        # options={"num_predict": max_tokens, "temperature": 0.1}
        options={"temperature": 0}
    )
    answer = response["message"]["content"]
    print(answer)
    return answer


st.title("音声文字起こしアプリ (whisper.cpp 使用)")
# 言語選択
language_map = {
    "日本語": "ja",
    "英語": "en",
    "スペイン語": "es",
    "フランス語": "fr",
    "中国語": "zh",
    "韓国語": "ko"
}
language_display = st.selectbox("音声の言語を選択してください", list(language_map.keys()))
language_code = language_map[language_display]
# 音声ファイルアップロード
uploaded_file = st.file_uploader("音声ファイルをアップロード", type=["mp3", "wav", "m4a"])
if uploaded_file is not None:
    # 一時ファイルに保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    st.info("文字起こし中...しばらくお待ちください")
    # whisper.cpp を使って文字起こし実行
    result = subprocess.run(
        [
            "whisper.cpp/bin/whisper-cli",
            "-m", "whisper.cpp/models/ggml-large-v3.bin",
            "-f", tmp_path,
            "-l", language_code,
            "--no-timestamps"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    os.remove(tmp_path)  # 一時ファイルを削除
    if result.returncode == 0:
        transcription = result.stdout.strip()
        st.success("文字起こし完了！編集してください")
        edited_text = st.text_area("文字起こし結果（編集可能）", transcription, height=300)
        if st.button("この内容で翻訳する"):
            with st.spinner("翻訳中..."):
                summary = summarize_text(edited_text)
                st.subheader("翻訳結果")
                st.write(summary)
    else:
        st.error("文字起こし中にエラーが発生しました")
        st.text(result.stderr)