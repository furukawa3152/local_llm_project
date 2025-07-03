import ollama
response = ollama.chat(
    #model="hf.co/mmnga/cyberagent-DeepSeek-R1-Distill-Qwen-14B-Japanese-gguf",
    #model="hf.co/grapevine-AI/DeepSeek-R1-Distill-Qwen-32B-Japanese-GGUF",
    #model= "gemma:7b",
    model= "Llama-Gemma-2-27b-ORPO-iter3.Q6_K.gguf:latest",
    messages=[
        {"role": "user", "content": "僕は何のために生きてるんだろう"},
    ],
    options={
        "num_predict" :200,
        "temperature" :0.1,
    }
)
print(response["message"]["content"])