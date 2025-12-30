from transformers import pipeline
import torch

class SimpleLLM:
    def __init__(self):
        # Используем маленькую модель для быстрого старта
        print("Загружаю модель... (это займет несколько минут)")
        
        self.pipe = pipeline(
            "text-generation",
            model="IlyaGusev/saiga_llama3_8b",
            device_map="auto",
            torch_dtype=torch.float16,
            model_kwargs={"load_in_8bit": True}  # Для экономии памяти
        )
        print("Модель загружена!")
    
    def quick_advice(self, prompt):
        """Генерирует краткий совет"""
        try:
            result = self.pipe(
                prompt,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True
            )
            return result[0]['generated_text']
        except Exception as e:
            return f"Ошибка генерации: {e}"

# Тест
if __name__ == "__main__":
    llm = SimpleLLM()
    test_prompt = "Привет! Как дела?"
    response = llm.quick_advice(test_prompt)
    print("Ответ модели:", response)