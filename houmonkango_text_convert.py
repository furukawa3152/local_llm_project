from janome.tokenizer import Tokenizer
import re
import ollama
from datetime import datetime, timedelta
from md2text import markdown_to_plain_text

from datetime import datetime, timedelta

def wareki_to_date(wareki_str):
    """
    和暦（令和7年04月05日）を datetime 型に変換
    """
    match = re.match(r"令和(\d+)年(\d{2})月(\d{2})日", wareki_str)
    if not match:
        return None
    year = int(match.group(1)) + 2018  # 令和元年=2019年
    month = int(match.group(2))
    day = int(match.group(3))
    return datetime(year, month, day)

def is_wareki_date(tokens, i):
    """
    tokens[i] から順に ['令和X年', 'XX月', 'XX日'] という形式で並んでいるか判定
    """
    if i + 2 >= len(tokens):
        return False
    pattern1 = re.match(r"令和\d+年", tokens[i])
    pattern2 = re.match(r"\d{2}月", tokens[i + 1])
    pattern3 = re.match(r"\d{2}日", tokens[i + 2])
    return all([pattern1, pattern2, pattern3])

def wareki_split_text_by_words(text, max_words):
        tokenizer = Tokenizer()

        # トークンとその開始位置を記録
        tokens = []
        positions = []

        offset = 0
        for token in tokenizer.tokenize(text, wakati=True):
            start = text.find(token, offset)
            if start == -1:
                continue
            tokens.append(token)
            positions.append(start)
            offset = start + len(token)

        split_texts = []
        start_char_pos = 0
        word_idx = 0

        while word_idx < len(tokens):
            if word_idx + max_words >= len(tokens):
                # 最後まで届かない場合は残り全てを追加
                split_texts.append(text[start_char_pos:].strip())
                break

            # 1000語目の位置
            approx_end_char_pos = positions[word_idx + max_words]

            # その後の部分から「令和X年XX月XX日」形式の最初の出現を探す
            match = re.search(r"(令和|平成|昭和)\d+年\d{2}月\d{2}日", text[approx_end_char_pos:])
            if match:
                # 分割点をその直前に設定（全文における文字インデックス）
                date_pos_in_full = approx_end_char_pos + match.start()
                segment = text[start_char_pos:date_pos_in_full].strip()
                split_texts.append(segment)
                start_char_pos = date_pos_in_full  # 次のスタートは日付の位置（含む）
                # 次の語数開始位置を更新
                while word_idx < len(positions) and positions[word_idx] < start_char_pos:
                    word_idx += 1
            else:
                # 日付が見つからなければ、そのまま1000語で分割
                segment = text[start_char_pos:positions[word_idx + max_words]].strip()
                split_texts.append(segment)
                start_char_pos = positions[word_idx + max_words]
                word_idx += max_words

        return split_texts
MODEL_NAME = "Gemma3:12b"
#MODEL_NAME = "Llama-Gemma-2-27b-ORPO-iter3.Q8_0.gguf:latest"
#MODEL_NAME = "Llama-Gemma-2-27b-ORPO-iter3.Q6_K.gguf:latest"
def make_spleted_houkansummary(text_list: list):
    total_text = ""
    for text in text_list:
        response = ollama.chat(
            model="Gemma3:12b",
            messages=[
                {'role': 'system', 'content':"""
    あなたは医療記録の専門科です。以下は長期にわたる診療記録の一部です。
    このセグメントについて、以下の点を考慮して簡潔に要約してください。
    1，主要な症状、診断、治療方針及び治療の変化
    2，検査結果や重要な経過の記述
    3，日付、時間の流れなど、経過記録に必要な前後関係
    文字数は内容の重複を控えコンパクトに。500文字以下を目標にしてください。かつ全体の記録と連続性を保つようにしてください。創作は一切せず、事実データのみを書き出すこと。
    特に身体状況に関わるイベントは、日付をつけて記載すること。
    **但し、日付の情報が不明確である場合には日付を無視して入力されたデータのみ処理すること。**
    形式は必ず以下のものを利用してください。
    ***出力形式***
    **
    YYYY年mm月dd日～YYYY年mm月dd日のまとめ
    主要な症状、診断、治療方針及び治療の経過（処置については部位の別に記載すること。）、排泄（排尿・排便）へのケアの内容、必要な検査結果
    **
    """},
                {'role': 'user', 'content': text}
            ],
            options={"temperature": 0}
        )
        answer = markdown_to_plain_text(response["message"]["content"])
        print(answer)
        total_text += answer + "\n\n"  # 回答を連結
    return total_text  # 最後に全体の要約を返す

def convert_era_line(text):
    lines = text.splitlines()
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 「令和」で始まる行を探す
        match = re.match(r"令和\s*(\d+)\s*(\d+)\s*(\d+)\s*(\S+)\s*(\d+)\s*(\d+)\s*(\d+)\s*(\d+)", line)
        if match:
            year, month, day, weekday, h1, m1, h2, m2 = match.groups()
            formatted = f"令和{year}年{month}月{day}日　{weekday}曜日　{h1}時{m1}分~{h2}時{m2}分"
            new_lines.append(formatted)
            i += 1

            # 次の行が「4つの数字」の行だったら変換
            if i < len(lines):
                next_line = lines[i]
                num_match = re.match(r"(\d+(?:\.\d+)?)\s+(\d+)\s+(\d+)\s+(\d+)", next_line)
                if num_match:
                    temp, pulse, bp_high, bp_low = num_match.groups()
                    summary = f"体温{temp}度、脈拍{pulse}、血圧{bp_high}/{bp_low}"
                    new_lines.append(summary)
                    i += 1
            continue

        new_lines.append(line)
        i += 1

    return "\n".join(new_lines)

def remove_fixed_block(text):
    pattern = re.compile(
        r"""訪問看護記録書Ⅱ\s*
            看護師等氏名\s*
            患\s*者\s*氏\s*名\s*
            同行スタッフ\s*
            訪\s*問\s*年\s*月\s*日\s*年\s*月\s*日（.*?）\s*時\s*分\s*～\s*時\s*分\s*
            バイタルサイン\s*体温\s*.*?血圧\s*／\s*
            写真添付欄１\s*写真添付欄２\s*
            次回の訪問予定日\s*年\s*月\s*日（.*?）\s*時\s*分\s*
            ページ中\s*ページ目\s*
            SpO2\(酸素飽和度\)\s*%""",
        re.VERBOSE | re.DOTALL
    )
    return pattern.sub("\n", text)

def process_text(text):
    text = remove_fixed_block(text)
    text = convert_era_line(text)
    return text


if __name__ == '__main__':
    text = """
    Janomeでトークンリスト（語数カウント用）だけを作成。

各トークンに対して、元のテキストでの開始位置と終了位置を記録。

1000語に達したら、その後に登場する日付のテキストインデックス位置を探し、

その位置で元のテキスト（非分割）を区切る。
... 令和7年04月05日 体温は36.5度。...
    """

    result = wareki_split_text_by_words(text,15)

    print(result)
