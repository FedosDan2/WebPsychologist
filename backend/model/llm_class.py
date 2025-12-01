from transformers import pipeline, BitsAndBytesConfig
import torch

class SimpleLLM:
    def __init__(self):
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
        self.pipe = pipeline(
            "text-generation",
            model="IlyaGusev/saiga_llama3_8b",
            device_map="auto",
            torch_dtype=torch.float16,
            quantization_config=quantization_config,
        )
        print("Модель загружена!")
    
    def quick_advice(self, prompt):
        try:
            result = self.pipe(
                prompt,
                max_new_tokens=512,
                temperature=0.8,
                do_sample=True,
                truncation=True,
                pad_token_id=128001  # для Llama3 — EOS = 128001
            )
            return result[0]['generated_text']
        except Exception as e:
            return f"Ошибка генерации: {e}"