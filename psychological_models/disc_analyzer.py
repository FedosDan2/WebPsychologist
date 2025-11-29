import json
import os
from collections import Counter

class DISCAnalyzer:
    def __init__(self):
        self.d_keywords = ["срочно", "результат", "контроль", "решаю", "быстро", "успех", "должны", "обязательно", "дедлайн", "план"]
        self.i_keywords = ["отлично", "супер", "круто", "вместе", "команда", "спасибо", "❤️", "😊", "😂", "рад", "привет"]
        self.s_keywords = ["спокойно", "помощь", "поддержка", "стабильность", "доверие", "понимаю", "ладно", "хорошо", "нормально"]
        self.c_keywords = ["анализ", "данные", "детали", "проверить", "точность", "отчёт", "проект", "интерфейс", "проверка", "числа"]
    
    def analyze_text(self, text, emotion_scores=None):
        """Анализирует текст и возвращает DISC баллы с учётом эмоций"""
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
        
        # УЧИТЫВАЕМ ЭМОЦИИ ИЗ JSON
        if emotion_scores:
            negative = emotion_scores.get('negative', 0)
            positive = emotion_scores.get('positive', 0)
            neutral = emotion_scores.get('neutral', 0)
            
            # Эмоции влияют на DISC баллы:
            if positive > 0.6:  # Сильно позитивное сообщение
                scores["I"] += 3  # Увеличиваем Influence
                scores["S"] += 1  # И немного Steadiness
            
            if negative > 0.6:  # Сильно негативное сообщение  
                scores["D"] += 2  # Увеличиваем Dominance (раздражение)
            
            if neutral > 0.8:  # Очень нейтральное сообщение
                scores["C"] += 2  # Увеличиваем Compliance (аналитичность)
                scores["S"] += 1  # И Steadiness (спокойствие)
        
        return scores
    
    def analyze_dialog_file(self, file_path):
        """Анализирует весь JSON файл диалога с учётом эмоций"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = {}
        emotion_analysis = {}  # Для хранения анализа эмоций
        
        for participant, info in data['participants_analysis'].items():
            all_scores = {"D": 0, "I": 0, "S": 0, "C": 0}
            emotion_stats = {
                'positive_messages': 0,
                'negative_messages': 0, 
                'neutral_messages': 0,
                'dominant_emotion': 'neutral'
            }
            
            # Анализируем все сообщения участника
            for message in info['messages']:
                text = message['text']
                emotion_scores = message.get('emotion_scores', {})
                
                # ПЕРЕДАЁМ ЭМОЦИИ В АНАЛИЗ
                message_scores = self.analyze_text(text, emotion_scores)
                
                # Анализируем эмоции
                if emotion_scores:
                    positive = emotion_scores.get('positive', 0)
                    negative = emotion_scores.get('negative', 0)
                    neutral = emotion_scores.get('neutral', 0)
                    
                    if positive > negative and positive > neutral:
                        emotion_stats['positive_messages'] += 1
                    elif negative > positive and negative > neutral:
                        emotion_stats['negative_messages'] += 1
                    else:
                        emotion_stats['neutral_messages'] += 1
                
                for style, score in message_scores.items():
                    all_scores[style] += score
            
            # Определяем доминирующую эмоцию
            total_messages = len(info['messages'])
            if total_messages > 0:
                pos_ratio = emotion_stats['positive_messages'] / total_messages
                neg_ratio = emotion_stats['negative_messages'] / total_messages
                
                if pos_ratio > neg_ratio and pos_ratio > 0.4:
                    emotion_stats['dominant_emotion'] = 'positive'
                elif neg_ratio > pos_ratio and neg_ratio > 0.4:
                    emotion_stats['dominant_emotion'] = 'negative'
                else:
                    emotion_stats['dominant_emotion'] = 'neutral'
            
            # Определяем доминирующий DISC стиль
            total = sum(all_scores.values())
            if total > 0:
                percentages = {style: (score / total) * 100 for style, score in all_scores.items()}
                dominant_style = max(all_scores.items(), key=lambda x: x[1])[0]
            else:
                percentages = {style: 0 for style in all_scores}
                dominant_style = "S"
            
            results[participant] = {
                'raw_scores': all_scores,
                'percentages': percentages,
                'dominant_style': dominant_style,
                'messages_count': info['messages_count'],
                'emotions_median': info['emotions_median'],
                'emotion_analysis': emotion_stats  # ДОБАВЛЯЕМ АНАЛИЗ ЭМОЦИЙ
            }
        
        return {
            'disc_results': results,
            'dialog_title': data.get('title', 'Без названия'),
            'raw_data': data
        }

    def get_emotional_insights(self, disc_results):
        """Генерирует инсайты на основе эмоций и DISC стилей"""
        insights = []
        
        for participant, data in disc_results.items():
            disc_style = data['dominant_style']
            emotion_stats = data.get('emotion_analysis', {})
            dominant_emotion = emotion_stats.get('dominant_emotion', 'neutral')
            
            # Сочетание DISC стиля и эмоций
            if disc_style == "D" and dominant_emotion == "negative":
                insights.append(f"🔴 {participant} (D-тип) проявляет негативные эмоции - может быть излишне требовательным")
            elif disc_style == "I" and dominant_emotion == "positive":
                insights.append(f"🟢 {participant} (I-тип) сохраняет позитив - отличный мотиватор команды")
            elif disc_style == "S" and dominant_emotion == "neutral":
                insights.append(f"🟡 {participant} (S-тип) сохраняет спокойствие - надежная опора в стрессе")
            elif disc_style == "C" and dominant_emotion == "negative":
                insights.append(f"🔴 {participant} (C-тип) испытывает негатив - возможно, перегружен деталями")
        
        return insights

# Тестирование с эмоциями
if __name__ == "__main__":
    analyzer = DISCAnalyzer()
    
    files = [
        "backend/analysis_results/1_analysis.json", 
        "backend/analysis_results/2_analysis.json"
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            print(f"\n=== Анализ файла: {file_path} ===")
            results = analyzer.analyze_dialog_file(file_path)
            
            for participant, data in results['disc_results'].items():
                print(f"\n👤 {participant}:")
                print(f"   🎭 Доминирующий стиль: {data['dominant_style']}")
                print(f"   📊 Распределение: {data['percentages']}")
                print(f"   😊 Эмоции: {data['emotions_median']}")
                print(f"   📈 Анализ эмоций: {data.get('emotion_analysis', {})}")
            
            # Выводим эмоциональные инсайты
            insights = analyzer.get_emotional_insights(results['disc_results'])
            if insights:
                print(f"\n💡 ЭМОЦИОНАЛЬНЫЕ ИНСАЙТЫ:")
                for insight in insights:
                    print(f"   • {insight}")