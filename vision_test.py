import ollama

response1 = ollama.chat(
    model = "Gemma3:latest",
    messages = [{
        "role": "user",
        "content": "この紹介状の中の日本語を読み込んで",
        "images": ["shoukaitest.jpg"],
    }],
)
print(response1["message"]["content"])

response2 = ollama.chat(
    model = "aya-expanse",
    messages = [{
        "role": "user",
        "content": "Translate into Japanese:\n" + response1["message"]["content"],
    }],
)
print(response2["message"]["content"])