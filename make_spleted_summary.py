from janome.tokenizer import Tokenizer
import re
import ollama
from datetime import datetime, timedelta
from md2text import markdown_to_plain_text

def split_text_by_week(text):
    """
    医療記録などの日付入りテキストを、1週間ごとに分割する関数。

    Parameters:
        text (str): 日付を含む長文の記録

    Returns:
        list of str: 各週ごとに分割されたテキストのリスト
    """
    # 日付パターン（例：2025-01-16）
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    date_positions = [(m.group(), m.start()) for m in date_pattern.finditer(text)]

    if not date_positions:
        return [text]

    # セグメント作成
    segments = []
    for i in range(len(date_positions)):
        date_str, start_pos = date_positions[i]
        end_pos = date_positions[i + 1][1] if i + 1 < len(date_positions) else len(text)
        segment_text = text[start_pos:end_pos]

        try:
            # 日付としてパースできるものだけ対象にする
            datetime.strptime(date_str, "%Y-%m-%d")
            segments.append((date_str, segment_text))
        except ValueError:
            # 前のセグメントがあればそこに連結、なければ無視
            if segments:
                segments[-1] = (segments[-1][0], segments[-1][1] + "\n" + segment_text)

    if not segments:
        return [text]

    # 最初の日付を基準にグループ化
    base_date = datetime.strptime(segments[0][0], "%Y-%m-%d")
    grouped = {}

    for date_str, segment_text in segments:
        try:
            current_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue  # この時点ではありえないが安全のため
        week_offset = (current_date - base_date).days // 7
        group_key = (base_date + timedelta(weeks=week_offset)).strftime("%Y-%m-%d")
        if group_key not in grouped:
            grouped[group_key] = ""
        grouped[group_key] += segment_text

    return [grouped[k] for k in sorted(grouped.keys())]


def split_text_by_words(text, max_words):
    """
    Janomeを使用してテキストを1000単語ごとに分割する。
    1000単語到達後、最初に登場する日付(YYYY-MM-DD)の手前で区切り、日付も含める。

    :param text: 入力テキスト (str)
    :param max_words: 最大単語数 (デフォルト: 1000)
    :return: 分割されたテキストのリスト (list)
    """
    tokenizer = Tokenizer()
    tokens = list(tokenizer.tokenize(text, wakati=True))  # 全単語をリスト化

    # 分割後のテキストリスト
    split_texts = []
    start_idx = 0

    while start_idx < len(tokens):
        end_idx = min(start_idx + max_words, len(tokens))  # 最大1000単語まで取得
        segment_tokens = tokens[start_idx:end_idx]
        segment_text = "".join(segment_tokens)

        # 1000単語以降に最初に登場する日付を探す
        remaining_text = "".join(tokens[end_idx:])  # 1000単語以降の部分
        date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", remaining_text)

        if date_match:
            # 日付の開始位置 (1000単語以降のテキスト内)
            date_pos_in_remaining = date_match.start()

            # 元のテキスト全体における日付の位置を計算
            full_text_before_date = "".join(tokens[:end_idx]) + remaining_text[:date_pos_in_remaining]
            date_pos_in_tokens = len(list(tokenizer.tokenize(full_text_before_date, wakati=True)))  # リスト化して単語数を取得

            # その手前までを1つのセグメントとする
            final_segment_tokens = tokens[start_idx:date_pos_in_tokens]
            final_segment_text = "".join(final_segment_tokens).rstrip()

            # 分割リストに追加
            split_texts.append(final_segment_text)

            # 次の開始位置を日付の位置に設定
            start_idx = date_pos_in_tokens
        else:
            # 日付が見つからない場合、そのまま区切る
            split_texts.append(segment_text)
            start_idx = end_idx

    return split_texts
MODEL_NAME = "Gemma3:27b"
#MODEL_NAME = "Llama-Gemma-2-27b-ORPO-iter3.Q8_0.gguf:latest"
#MODEL_NAME = "Llama-Gemma-2-27b-ORPO-iter3.Q6_K.gguf:latest"
def make_spleted_summary(text_list: list):
    total_text = ""
    for text in text_list:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content':"""
    あなたは医療記録の専門科です。以下は長期にわたる診療記録の一部です。
    このセグメントについて、以下の点を考慮して簡潔に要約してください。
    1，主要な症状、診断、治療方針及び治療の変化
    2，検査結果や重要な経過の記述
    3，日付、時間の流れなど、経過記録に必要な前後関係
    文字数は可能な限りコンパクトに。200文字以下を目標にしてください。かつ全体の記録と連続性を保つようにしてください。創作は一切せず、事実データのみを書き出すこと。
    形式は必ず以下のものを利用してください。
    ***出力形式***
    **
    YYYY年mm月dd日～YYYY年mm月dd日のまとめ
    主要な症状、診断、治療方針及び治療の経過、必要な検査結果
    **
    """},
                {'role': 'user', 'content': text}
            ],
            options={"temperature": 0}
        )
        answer = markdown_to_plain_text(response["message"]["content"])
        total_text += answer + "\n\n"  # 回答を連結
    return total_text  # 最後に全体の要約を返す

if __name__ == '__main__':
    text = """
    これはテストの文章です。長い文章を分割するためのサンプルです。
    ここではいくつかの単語を入れて1000語に到達するようにします。適当に文章を埋めていきます。
    2025-03-13 この日付が出る前に区切るようにしたい。
    さらに続けて文章を書きます。たとえば...
    2025-03-19 ここでまた新しい日付が出てきます。
    2025-03-20 ここでまた新しい日付が出てきます。
    2025-03-23 ここでまた新しい日付が出てきます。
    2025-03-30 ここでまた新しい日付が出てきます。
    """

    result = split_text_by_week(text)

    print(result)
