import streamlit as st
from PIL import Image
import io
import base64
import ollama
import pandas as pd
import json
import os
import re
# 複数の JSON オブジェクトをすべて抽出
def extract_json_objects(text: str):
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    return matches
# 画像 → base64 文字列に変換
def image_to_base64(img: Image.Image) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode()

# Ollama に画像を渡して読み取る
def extract_text_from_image(image: Image.Image) -> str:
    image_b64 = image_to_base64(image)
    response = ollama.chat(
        model="Gemma3:27b",
        messages=[{
            "role": "user",
            "content": "領収書の画像を与えます。商品名、金額、適用という項目を持つJson形式で出力してください。***必ずJSONだけを返してください。説明文やラベルは不要です。***",
            "images": [image_b64],
        }],
    )
    return response["message"]["content"]

# CSVファイルに書き込む
def append_to_csv(df: pd.DataFrame, filename: str):
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, mode='w', header=True, index=False)

# Streamlit UI
st.title("画像読み取り & 表形式で編集")

uploaded_file = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png"])
csv_filename = "receipt_data.csv"

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    if st.button("読み取り"):
        with st.spinner("処理中..."):
            extracted_text = extract_text_from_image(image)
            json_blocks = extract_json_objects(extracted_text)

            if not json_blocks:
                st.error("JSON形式のデータが見つかりませんでした。")
                st.stop()

            try:
                data_list = [json.loads(block) for block in json_blocks]
                df = pd.DataFrame(data_list)
                st.session_state["editable_df"] = df
            except Exception as e:
                st.error(f"JSON読み込みエラー: {e}")
                st.stop()

# 表の編集と保存処理
if "editable_df" in st.session_state:
    st.subheader("📝 抽出されたデータの確認と編集")
    edited_df = st.data_editor(st.session_state["editable_df"], num_rows="dynamic", use_container_width=True)

    if st.button("CSVに保存"):
        append_to_csv(edited_df, csv_filename)
        st.success(f"CSVに保存しました: {csv_filename}")
