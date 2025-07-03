from ollama_ocr import OCRProcessor
ocr = OCRProcessor(model_name='llama3.2-vision')
result = ocr.process_image("shoukaitest.jpg", format_type="structured")
print(result)