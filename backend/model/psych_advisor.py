from model.llm_class import SimpleLLM

class PsychAdvisor:
    def __init__(self):
        try:
            self.llm = SimpleLLM()
            self.llm_loaded = True
            self.analysis_text = None
        except Exception as e:
            print(f"Не удалось загрузить LLM: {e}")
            self.llm_loaded = False
    
    def format_analysis_for_llm(self, disc_results):
        """Форматирует результаты анализа для LLM"""
        
        analysis_text = f"Анализ диалога: \n\n"
        # "messages_count": len(messages_out),
        # "dominant_emotion" : dominant_emotion,
        # "emotions_median": emotions_median,
        # "text_dominant" : self.sender_disc_analyze[sender]["text_dominant"],
        # "test_dominant" : self.sender_disc_analyze[sender]["test_dominant"],
        # "type_descriptions" : self.type_descriptions,
        # "messages": messages_out
        for participant, data in disc_results.items():
            analysis_text += f"👤 {participant}:\n"
            analysis_text += f"   • Доминирующая эмоция: {data['dominant_emotion']}\n"
            analysis_text += f"   • Общая оценка эмоций по медиане: {data['emotions_median']}\n"
            analysis_text += f"   • Доминирующий стиль в общение чата: {data['text_dominant']}\n"
            analysis_text += f"   • Доминирующий стиль в результате проведенного теста: {data['test_dominant']}\n"
            analysis_text += f"   • Расшифровка стилей: {data['type_descriptions']}\n"
            analysis_text += f"   • Сообщений: {data['messages_count']}\n\n"
        
        return analysis_text
    
    def get_recommendations(self, disc_results):
        """Получает рекомендации от LLM на основе анализа"""
        
        if not self.llm_loaded:
            return "LLM не загружена. Используйте демо-режим."
        
        analysis_text = self.format_analysis_for_llm(disc_results)
        
        prompt = f"""
Ты — психолог-консультант. Проанализируй стили общения DISC, эмоциональный уровень диалога и дай практические рекомендации.

ДАННЫЕ АНАЛИЗА:
{analysis_text}

Дай ответ в формате:
ОСНОВНЫЕ ТЕМЫ РАЗГОВОРА:

КЛЮЧЕВЫЕ ИНСАЙТЫ:
- Основные наблюдения о коммуникации

РЕКОМЕНДАЦИИ:
1. Совет 1
2. Совет 2  
3. Совет 3

🗣️ ПРИМЕРЫ ФРАЗ:
- Что говорить в подобных ситуациях

Будь практичным и конкретным:
"""
        
        try:
            advice = self.llm.quick_advice(prompt)
            return advice
        except Exception as e:
            return f"Ошибка при генерации советов: {e}"