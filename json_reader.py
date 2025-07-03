# streamlit_app.py
import streamlit as st
import os
import json
import pandas as pd

# チャットログを読み込んでDataFrame化する関数
def load_chat_logs(directory):
    data = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    chat_data = json.load(f)
                    for session_time, session_info in chat_data.items():
                        messages = session_info.get("messages", [])
                        rating = session_info.get("rating", "norate")  # None の代わりに "norate"

                        user_msgs = [m['content'] for m in messages if m['role'] == 'user']
                        assistant_msgs = [m['content'] for m in messages if m['role'] == 'assistant']

                        data.append({
                            "ファイル名（ユーザー名）": filename.replace(".json", ""),
                            "開始時刻": session_time,
                            "ユーザー発言": "\n".join(user_msgs),
                            "アシスタント応答": "\n".join(assistant_msgs),
                            "評価（rating）": rating
                        })
                except Exception as e:
                    st.warning(f"ファイルの読み込みエラー: {filename} - {e}")
    return pd.DataFrame(data)

# Streamlit アプリ本体
st.title("Chat Logs Viewer")

directory_path = "chat_logs"

if not os.path.exists(directory_path):
    st.error(f"ディレクトリが見つかりません: {directory_path}")
else:
    df = load_chat_logs(directory_path)

    if df.empty:
        st.info("チャットログが見つかりませんでした。")
    else:
        # 評価でフィルタ（"norate" を含む）
        rating_options = sorted(df["評価（rating）"].astype(str).unique())
        selected_ratings = st.multiselect("表示する評価（rating）を選んでください", rating_options,
                                          default=rating_options)

        filtered_df = df[df["評価（rating）"].astype(str).isin(selected_ratings)]

        st.dataframe(filtered_df, use_container_width=True)

        selected_row = st.selectbox("詳細を表示するチャットセッションを選んでください", filtered_df["開始時刻"])

        if selected_row:
            row_data = filtered_df[filtered_df["開始時刻"] == selected_row].iloc[0]
            st.subheader("ユーザー発言")
            st.text(row_data["ユーザー発言"])
            st.subheader("アシスタント応答")
            st.text(row_data["アシスタント応答"])
