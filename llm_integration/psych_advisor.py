from .local_llm import SimpleLLM
import json

class PsychAdvisor:
    def __init__(self):
        self.llm = SimpleLLM()
    
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
        
        analysis_text = self.format_analysis_for_llm(disc_results, dialog_title)
        
        prompt = f"""
Проанализируй стили общения и дай практические рекомендации:

{analysis_text}

Дай ответ в формате:
1. Ключевые инсайты о коммуникации
2. 2-3 конкретные рекомендации для улучшения общения
3. Примеры фраз, которые стоит использовать

Будь практичным и конкретным:
"""
        
        try:
            advice = self.llm.quick_advice(prompt)
            return advice
        except Exception as e:
            return f"Ошибка при генерации советов: {e}"

# Тест с твоими реальными данными
if __name__ == "__main__":
    # Пока ждём загрузку модели, протестируем на mock данных
    advisor = PsychAdvisor()
    
    # Mock результаты анализа (замени на реальные из disc_analyzer.py)
    mock_results = {
        "Алексей": {
            'dominant_style': "D",
            'messages_count': 10,
            'emotions_median': {'negative': 0.05, 'neutral': 0.65, 'positive': 0.20},
            'percentages': {'D': 60, 'I': 20, 'S': 10, 'C': 10}
        },
        "Ирина": {
            'dominant_style': "S", 
            'messages_count': 10,
            'emotions_median': {'negative': 0.06, 'neutral': 0.36, 'positive': 0.49},
            'percentages': {'D': 10, 'I': 30, 'S': 50, 'C': 10}
        }
    }
    
    print("Форматированный анализ для LLM:")
    formatted = advisor.format_analysis_for_llm(mock_results, "Начальник и сотрудница")
    print(formatted)
    
    # Когда модель загрузится, раскомментируй:
    # advice = advisor.get_recommendations(mock_results, "Начальник и сотрудница")
    # print("\nРЕКОМЕНДАЦИИ ОТ LLM:")
    # print(advice)