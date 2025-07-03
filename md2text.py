import re


def markdown_to_plain_text(md_content):
    """マークダウン記法を削除し、通常のテキストに変換"""
    # 見出し（# で始まる行）を削除
    md_content = re.sub(r'^#+\s+', '', md_content, flags=re.MULTILINE)
    # 強調（**または*）を削除
    md_content = re.sub(r'\*\*(.*?)\*\*', r'\1', md_content)
    md_content = re.sub(r'\*(.*?)\*', r'\1', md_content)
    # リンクをテキストのみに変換
    md_content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', md_content)
    # 画像を削除
    md_content = re.sub(r'!\[.*?\]\(.*?\)', '', md_content)
    # リストの記号を削除
    md_content = re.sub(r'^\s*[-*+]\s+', '', md_content, flags=re.MULTILINE)
    # 番号付きリストの記号を削除
    md_content = re.sub(r'^\s*\d+\.\s+', '', md_content, flags=re.MULTILINE)
    # コードブロックを削除（バッククォート）
    md_content = re.sub(r'`{1,3}([^`]+)`{1,3}', r'\1', md_content)
    # 改行を適切に処理
    md_content = re.sub(r'\n{2,}', '\n', md_content).strip()

    return md_content


# 例
md_text = """
# タイトル
これは **強調** されたテキストです。

## 小見出し
- リスト1
- リスト2
[リンク](https://example.com)
"""

plain_text = markdown_to_plain_text(md_text)
print(plain_text)
