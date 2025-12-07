from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

class LightRussianLLM:
    def __init__(self, model_size="tiny"):
        """
        model_size варианты:
        - 'tiny': 1.1 GB (TinyLlama) - самый лёгкий
        - 'small': 3 GB (mGPT) - баланс качество/размер
        - 'medium': 7 GB (Saiga 7B) - лучшее качество
        """
        
        model_map = {
            'tiny': "ai-forever/TinyLlama-1.1B-Chat-v1.0",      # 1.1 GB
            'small': "ai-forever/mGPT",                         # 3 GB
            'medium': "IlyaGusev/saiga_mistral_7b_gguf"         # 4 GB
        }
        
        self.model_name = model_map.get(model_size, model_map['tiny'])
        
        print(f" Загружаю модель: {self.model_name}")
        print(f" Примерный размер: {self.get_model_size(model_size)}")
        
        try:
            self.pipe = pipeline(
                "text-generation",
                model=self.model_name,
                torch_dtype=torch.float16,  # Используем половинную точность
                device_map="auto",          # Автовыбор устройства
                model_kwargs={"load_in_8bit": True} if model_size == 'medium' else {}
            )
            print(" Модель успешно загружена!")
        except Exception as e:
            print(f" Ошибка загрузки модели: {e}")
            print(" Пробую загрузить без GPU...")
            self.pipe = pipeline(
                "text-generation",
                model=self.model_name,
                device=-1  # Использовать только CPU
            )
    
    def get_model_size(self, size):
        sizes = {
            'tiny': "1.1 GB (работает на любом ПК)",
            'small': "3 GB (нужно 8+ GB RAM)", 
            'medium': "4 GB (нужно 16+ GB RAM)"
        }
        return sizes.get(size, "неизвестно")
    
    def generate_psych_advice(self, analysis_text):
        """Генерирует психологические рекомендации"""
        
        prompt = f"""
Ты психолог-консультант. Проанализируй данные и дай рекомендации:

{analysis_text}

Дай 2-3 конкретных совета для улучшения общения.
Будь кратким и практичным.
"""
        
        try:
            result = self.pipe(
                prompt,
                max_new_tokens=150,  # Короткий ответ для экономии памяти
                temperature=0.7,
                do_sample=True
            )
            return result[0]['generated_text']
        except Exception as e:
            return f" Ошибка генерации: {e}\n💡 Попробуй использовать model_size='tiny'"

# Тест самой лёгкой модели
if __name__ == "__main__":
    print("🧪 Тест самой лёгкой русской модели...")
    
    # Попробуй сначала tiny, если не работает - small
    llm = LightRussianLLM(model_size="tiny")
    
    test_analysis = """
    Алексей: D-тип (решительный), говорит быстро, прямолинейно.
    Ирина: S-тип (поддерживающий), говорит мягко, часто извиняется.
    """
    
    advice = llm.generate_psych_advice(test_analysis)
    print("\n РЕКОМЕНДАЦИИ ОТ ЛЁГКОЙ МОДЕЛИ:")
    print("-" * 40)
    print(advice)
    print("-" * 40)