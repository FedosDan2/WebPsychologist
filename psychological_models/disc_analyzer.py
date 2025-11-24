import json
import os
from collections import Counter

class DISCAnalyzer:
    def __init__(self):
        self.d_keywords = ["срочно", "результат", "контроль", "решаю", "быстро", "успех", "должны", "обязательно"]
        self.i_keywords = ["отлично", "супер", "круто", "вместе", "команда", "спасибо", "❤️", "😊", "😂"]
        self.s_keywords = ["спокойно", "помощь", "поддержка", "стабильность", "доверие", "понимаю", "ладно"]
        self.c_keywords = ["анализ", "данные", "детали", "проверить", "точность", "отчёт", "проект", "интерфейс"]
    
    def analyze_text(self, text):
        """Анализирует текст и возвращает DISC баллы"""
        text = text.lower()
        scores = {"D": 0, "I": 0, "S": 0, "C": 0}
        
        # Анализ ключевых слов
        for word in self.d_keywords:
            if word in text:
                scores["D"] += 2
        
        for word in self.i_keywords:
            if word in text:
                scores["I"] += 2
            # Эмодзи и восклицания
            if "!" in text:
                scores["I"] += text.count("!")
            if "😊" in text or "😂" in text or "❤️" in text:
                scores["I"] += 3
        
        for word in self.s_keywords:
            if word in text:
                scores["S"] += 2
        
        for word in self.c_keywords:
            if word in text:
                scores["C"] += 2
            # Вопросы и детализация
            if "?" in text:
                scores["C"] += text.count("?")
        
        return scores
    
    def analyze_dialog_file(self, file_path):
        """Анализирует весь JSON файл диалога"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
        results = {}
        
        for participant, info in data['participants_analysis'].items():
            all_scores = {"D": 0, "I": 0, "S": 0, "C": 0}
            
            # Анализируем все сообщения участника
            for message in info['messages']:
                text = message['text']
                message_scores = self.analyze_text(text)
                
                for style, score in message_scores.items():
                    all_scores[style] += score
            
            # Определяем доминирующий стиль
            total = sum(all_scores.values())
            if total > 0:
                percentages = {style: (score / total) * 100 for style, score in all_scores.items()}
                dominant_style = max(all_scores.items(), key=lambda x: x[1])[0]
            else:
                percentages = {style: 0 for style in all_scores}
                dominant_style = "S"  # по умолчанию
            
            # ВОЗВРАЩАЕМ ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ
        return {
        'disc_results': results,
        'dialog_title': data.get('title', 'Без названия'),
        'raw_data': data  # на всякий случай
        }
        
    

def compare_with_self_assessment(real_style, self_assessment):
    """Сравнивает реальный стиль с самооценкой"""
    comparison = {
        'match': real_style == self_assessment,
        'real_style': real_style,
        'self_assessment': self_assessment
    }
    
    if real_style != self_assessment:
        style_descriptions = {
            "D": "решительный, ориентированный на результат",
            "I": "общительный, эмоциональный", 
            "S": "стабильный, поддерживающий",
            "C": "аналитичный, системный"
        }
        comparison['insight'] = (
            f"Вы считаете себя {style_descriptions[self_assessment]}, "
            f"но в переписке проявляетесь как {style_descriptions[real_style]}"
        )
    
    return comparison

# Тестирование на реальных данных
if __name__ == "__main__":
    analyzer = DISCAnalyzer()
    
    # Протестируем на обоих файлах
    files = [
        "backend/analysis_results/1_analysis.json", 
        "backend/analysis_results/2_analysis.json"
    ]
    
    for file in files:
        if os.path.exists(file):
            print(f"\n=== Анализ файла: {file} ===")
            results = analyzer.analyze_dialog_file(file)
            
            for participant, data in results.items():
                print(f"\n👤 {participant}:")
                print(f"   Доминирующий стиль: {data['dominant_style']}")
                print(f"   Распределение: {data['percentages']}")
                print(f"   Сообщений: {data['messages_count']}")
                print(f"   Эмоции: {data['emotions_median']}")
        else:
            print(f"Файл {file} не найден, проверь путь")