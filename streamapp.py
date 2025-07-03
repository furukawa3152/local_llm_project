import streamlit as st
import ollama
import os
import json
import pandas as pd
from datetime import datetime

# ✅ **最初に `st.set_page_config()` を実行**
st.set_page_config(page_title="AI chat", layout="wide")
st.title("Non-Internet AI chat")

# CSVからユーザー情報を読み込み
users = {}

if os.path.exists('users.csv'):
    df_users = pd.read_csv('users.csv')
    users = {row['username']: {"name": row['name'], "password": row['password']} for _, row in df_users.iterrows()}
else:
    st.error("ユーザー情報のCSVファイルが見つかりません。")

# ログインフォーム
username = st.sidebar.text_input("ユーザー名")
password = st.sidebar.text_input("パスワード", type="password")
login_button = st.sidebar.button("ログイン")

# 認証ステータス
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False

if login_button:
    if username in users and password == users[username]['password']:
        st.session_state['authentication_status'] = True
        st.session_state['name'] = users[username]['name']
        st.session_state['username'] = username  # ユーザー名をセッションに保存
    else:
        st.session_state['authentication_status'] = False
        st.error("ユーザー名かパスワードが間違っています")

# 認証後の処理
if st.session_state['authentication_status']:
    st.sidebar.write(f"{st.session_state['name']} さん、ようこそ！")
    logout_button = st.sidebar.button("ログアウト")

    if logout_button:
        st.session_state['authentication_status'] = False
        st.rerun()

    # ログを保存するディレクトリ
    LOG_DIR = "chat_logs"
    os.makedirs(LOG_DIR, exist_ok=True)

    # **ユーザーごとの履歴ファイル**
    history_file = os.path.join(LOG_DIR, f"{st.session_state['username']}.json")


    # **現在の時刻を取得**
    def get_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    # **履歴を読み込む関数**
    def load_chat_history(file_path):
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}


    def save_chat_history(file_path, username, messages, rating=None, timestamp=None):
        history = load_chat_history(file_path)
        if timestamp is None:
            timestamp = get_timestamp()  # fallback

        log_entry = {"messages": messages.copy()}
        if rating is not None:
            log_entry["rating"] = rating

        history[timestamp] = log_entry

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)


    tab1, tab2 = st.tabs(["チャット", "使い方"])

    with tab1:
        # **アプリ起動時に履歴を読み込む**
        history_data = load_chat_history(history_file)

        # **会話のリセット**
        if "messages" not in st.session_state:
            st.session_state.messages = []

            # **システムプロンプトを追加**
            system_prompt = {
                "role": "system",
                "content": "日本語で回答してください。ハルシネーションは禁止します。また、参考リンク等は添付しないこと。***重要***　**知識の無い人名に対する問い合わせは、必ず「不明です」というのみにしてください。**",
                "timestamp": get_timestamp()
            }
            st.session_state.messages.append(system_prompt)

        # **会話のリセット**
        if st.button("🗑 会話をリセット"):
            st.session_state.messages = [st.session_state.messages[0]]  # システムプロンプトのみ保持
            st.rerun()

        # 履歴の表示
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f"**あなた**: {message['content']}")
            elif message["role"] == "assistant":
                with st.chat_message("assistant"):
                    st.markdown(f"{message['content']} ")

        # ユーザーの入力
        user_input = st.chat_input("メッセージを入力してください...")

        if user_input:
            if len(user_input) > 3000:
                st.warning("3000字以内で入力してください。")
            else:
                timestamp = get_timestamp()

                # ユーザーのメッセージを保存
                user_message = {"role": "user", "content": user_input, "timestamp": timestamp}
                st.session_state.messages.append(user_message)

                # 表示
                with st.chat_message("user"):
                    st.markdown(f"**あなた**: {user_input}")

                # AIの応答をストリーミング表示
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    bot_message = ""

                    try:
                        for chunk in ollama.chat(model="Gemma3:latest", messages=st.session_state.messages, stream=True):
                            if "message" in chunk and "content" in chunk["message"]:
                                bot_message += chunk["message"]["content"]
                                message_placeholder.markdown(bot_message + "▌")
                            else:
                                st.error("Ollama APIのレスポンスが予期しない形式です")
                    except Exception as e:
                        st.error(f"Ollama APIのエラー: {e}")

                    message_placeholder.markdown(bot_message)

                # AIのメッセージを履歴に保存
                ai_message = {"role": "assistant", "content": bot_message, "timestamp": get_timestamp()}
                st.session_state.messages.append(ai_message)

                # 会話ログを保存（評価はこの時点では未記入）
                st.session_state["latest_timestamp"] = timestamp
                save_chat_history(
                    history_file,
                    st.session_state['username'],
                    st.session_state.messages,
                    rating=None,
                    timestamp=st.session_state["latest_timestamp"]
                )

                # 評価フォーム表示フラグ
                st.session_state["show_rating_form"] = True

        # チャット評価スライダーの表示と保存処理（会話後）
        if st.session_state.get("show_rating_form", False):
            with st.form(key=f"rating_form_{st.session_state['latest_timestamp']}"):
                st.markdown(" チャットの最後に10段階でこの回答の評価をしてください")
                st.markdown("（1：全く欲しい回答でなかった。～10：完全に必要な処理をしてくれた）")
                rating = st.slider("評価", min_value=1, max_value=10, value=5)
                submitted = st.form_submit_button("評価を送信")

                if submitted:
                    st.success(f"評価 {rating} を送信しました。")
                    st.session_state["last_rating"] = rating  # 評価を一時保存
                    st.session_state["show_rating_form"] = False  # フォーム非表示に
                    st.rerun()  # 再読み込みして保存処理へ

        # 評価があれば履歴と一緒に保存
        if "last_rating" in st.session_state:
            rating_to_save = st.session_state.pop("last_rating")
            target_timestamp = st.session_state.pop("latest_timestamp", get_timestamp())

            save_chat_history(
                history_file,
                st.session_state['username'],
                st.session_state.messages,
                rating=rating_to_save,
                timestamp=target_timestamp
            )


    with tab2:
        st.markdown("""
                # 利用のコツ\n\nAIに指示を出す際、以下の点を意識することで、より期待通りのアウトプットを得やすくなります。
                \n\n**1. 目的を明確に伝える:**\n\n*   **悪い例:** 「この文章をどうにかして」
                \n*   **良い例:** 「以下の文章を300字以内で要約してください。」\n    *   「要約」「翻訳」「校正」「創作」など、具体的な目的を明示します。\n\n**2. 役割を与える:**
                \n\n*   AIに特定の役割を与えることで、文体や視点が変化します。\n*   例: 「あなたは弁護士です。以下の契約書を読み解き、問題点があれば指摘してください。」\n\n**3. 具体例を入れる:**
                \n\n*   期待する出力の「イメージ」を伝えることで、AIはより的確なアウトプットを生成できます。\n*   例: 「以下のようなフォーマットで回答してください： 箇条書き、表形式など」
                \n\n**4. 制約条件を加える:**\n\n*   長さ、形式、トーン（丁寧／カジュアル）、ターゲット層など、出力の条件を明確に指定します。
                \n*   例: 「100文字以内で、ビジネスシーンに合わせた丁寧な表現で」\n\n**5. 段階的に指示を出す（ステップ・バイ・ステップ）:**
                \n\n*   複雑な指示は、複数のステップに分けて、段階的に進めることで、精度が向上します。\n*   例：\n    *   ステップ1：文章の要約\n    *   ステップ2：要約した文章の校正
                \n    *   ステップ3：校正した文章の修正
                \n\n  *   ご意見、ご要望あれば医事課古川までお知らせください。
        """)


elif not login_button:
    st.sidebar.warning('ユーザー名とパスワードを入力してください')






