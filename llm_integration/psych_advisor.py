from .local_llm import SimpleLLM

class PsychAdvisor:
    def __init__(self):
        try:
            self.llm = SimpleLLM()
            self.llm_loaded = True
        except Exception as e:
            print(f"Не удалось загрузить LLM: {e}")
            self.llm_loaded = False
    
    def format_analysis_for_llm(self, disc_results, dialog_title):
        """Форматирует результаты анализа для LLM"""
        
        analysis_text = f"Анализ диалога: {dialog_title}\n\n"
        
        for participant, data in disc_results.items():
            analysis_text += f"👤 {participant}:\n"
            analysis_text += f"   • Доминирующий стиль: {data['dominant_style']}\n"
            analysis_text += f"   • Сообщений: {data['messages_count']}\n"
            analysis_text += f"   • Эмоции: {data['emotions_median']}\n"
            analysis_text += f"   • Распределение стилей: {data['percentages']}\n\n"
        
        return analysis_text
    
    def get_recommendations(self, disc_results, dialog_title):
        """Получает рекомендации от LLM на основе анализа"""
        
        if not self.llm_loaded:
            return "LLM не загружена. Используйте демо-режим."
        
        analysis_text = self.format_analysis_for_llm(disc_results, dialog_title)
        
        prompt = f"""
Ты — психолог-консультант. Проанализируй стили общения DISC и дай практические рекомендации.

ДАННЫЕ АНАЛИЗА:
{analysis_text}

Дай ответ в формате:
КЛЮЧЕВЫЕ ИНСАЙТЫ:
- Основные наблюдения о коммуникации

РЕКОМЕНДАЦИИ:
1. Конкретный совет 1
2. Конкретный совет 2  
3. Конкретный совет 3

🗣️ ПРИМЕРЫ ФРАЗ:
- Что говорить в подобных ситуациях

Будь практичным и конкретным:
"""
        
        try:
            advice = self.llm.quick_advice(prompt)
            return advice
        except Exception as e:
            return f"Ошибка при генерации советов: {e}"

# Тест
if __name__ == "__main__":
    advisor = PsychAdvisor()
    
    mock_results = {
        "Алексей": {
            'dominant_style': "D",
            'messages_count': 10,
            'emotions_median': {'negative': 0.05, 'neutral': 0.65, 'positive': 0.20},
            'percentages': {'D': 60, 'I': 20, 'S': 10, 'C': 10}
        }
    }
    
    print("Форматированный анализ:")
    print(advisor.format_analysis_for_llm(mock_results, "Тест"))