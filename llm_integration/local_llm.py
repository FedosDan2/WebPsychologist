from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

class LocalLLM:
    def __init__(self):
        self.model_name = "IlyaGusev/saiga_llama3_8b"  # Русская модель
        # Или: "mistralai/Mistral-7B-Instruct-v0.2" (английская)
        
        print("Загружаю модель... (это займет несколько минут)")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        
        self.chat_pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=256,
            temperature=0.7
        )
        
        print("Модель загружена!")
    
    def generate_psych_advice(self, disc_analysis, dialog_context):
        """Генерирует психологические рекомендации на основе анализа"""
        
        prompt = f"""
Ты — психолог-консультант. Проанализируй стили общения и дай рекомендации.

ДАННЫЕ АНАЛИЗА:
{disc_analysis}

КОНТЕКСТ ДИАЛОГА:
{dialog_context}

СФОРМУЛИРУЙ:
1. Основные инсайты о стилях общения
2. 2-3 практические рекомендации для улучшения коммуникации
3. Конкретные фразы, которые стоит использовать

Ответь на русском, будь конкретным и практичным:
"""
        
        response = self.chat_pipeline(
            prompt,
            max_new_tokens=300,
            temperature=0.7,
            do_sample=True
        )
        
        return response[0]['generated_text']

# Упрощённая версия для быстрого теста
class SimpleLLM:
    def __init__(self):
        # Самая лёгкая модель для быстрого старта
        self.pipe = pipeline(
            "text-generation",
            model="IlyaGusev/saiga_llama3_8b",
            device_map="auto",
            torch_dtype=torch.float16
        )
    
    def quick_advice(self, analysis_text):
        prompt = f"Как психолог, дай краткий совет: {analysis_text}"
        
        result = self.pipe(
            prompt,
            max_new_tokens=150,
            temperature=0.7
        )
        return result[0]['generated_text']


if __name__ == "__main__":
    # Тест с упрощённой моделью
    llm = SimpleLLM()
    
    test_analysis = """
    Алексей: тип D (решительный), Ирина: тип S (поддерживающий)
    Алексей часто даёт прямые указания, Ирина извиняется за ошибки.
    """
    
    advice = llm.quick_advice(test_analysis)
    print("СОВЕТ ОТ LLM:")
    print(advice)


# Для слабых компьютеров:
# "Qwen/Qwen2.5-0.5B"  # Очень лёгкая
# "mistralai/Mistral-7B-Instruct-v0.2"  # Баланс качество/скорость