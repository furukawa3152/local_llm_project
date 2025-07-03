import ollama
from io import BytesIO

# ネットワーク上の画像パス（Windows UNCパス → POSIX形式に変換）
image_path = r"smb://172.16.70.20/入院費関係/DSC_0211.JPG"

# 画像を開いて `BytesIO` に変換
with open(image_path, "rb") as f:
    image_data = BytesIO(f.read())

# Ollama に画像を渡す
response1 = ollama.chat(
    model="llama3-2-vision",
    messages=[{
        "role": "user",
        "content": "What is in this image?",
        "images": [image_data],  # `BytesIO` を渡す
    }],
)

# 結果を取得
description = response1["message"]["content"]
print(description)
