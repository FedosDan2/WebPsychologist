import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from psychological_models.disc_analyzer import DISCAnalyzer
from psychological_models.topic_analyzer import TopicAnalyzer
from llm_integration.psych_advisor import PsychAdvisor

class UnifiedAnalyzer:
    """Объединяет все виды анализа в один отчет"""
    
    def __init__(self):
        self.disc_analyzer = DISCAnalyzer()
        self.topic_analyzer = TopicAnalyzer()
        self.psych_advisor = PsychAdvisor()
    
    def analyze_dialog(self, file_path):
        """Полный анализ диалога"""
        print(f"\n{'='*60}")
        print(f" ПОЛНЫЙ АНАЛИЗ ДИАЛОГА: {os.path.basename(file_path)}")
        print('='*60)
        
        # 1. DISC анализ
        print("\n АНАЛИЗ ПСИХОЛОГИЧЕСКИХ СТИЛЕЙ (DISC):")
        disc_results = self.disc_analyzer.smart_analyze(file_path)
        
        for participant, data in disc_results['disc_results'].items():
            print(f"    {participant}: {data['dominant_style']}-тип")
            print(f"      Распределение: {data['percentages']}")
        
        # 2. Анализ тем
        print("\n АНАЛИЗ ТЕМ РАЗГОВОРА:")
        
        # Загружаем данные для анализа тем
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'messages' in data:
            messages = data['messages']
            participants = data.get('participants', [])
        elif 'participants_analysis' in data:
            messages = []
            participants = []
            for participant, info in data['participants_analysis'].items():
                participants.append(participant)
                for msg in info['messages']:
                    messages.append({
                        'sender': participant,
                        'text': msg['text']
                    })
        else:
            messages = []
            participants = []
        
        topic_results = self.topic_analyzer.analyze_dialog_topics(messages, participants)
        
        print(f"   Основные темы:")
        for topic in topic_results['dominant_topics'][:3]:  # Топ-3 темы
            print(f"      • {topic['topic']} ({topic['count']} упоминаний)")
        
        print(f"\n   Что интересует участников:")
        for participant, interests in topic_results['participant_interests'].items():
            print(f"      {participant}: {interests['main_interest']}")
        
        # 3. Генерация рекомендаций с учетом тем
        print("\nИНТЕГРИРОВАННЫЕ РЕКОМЕНДАЦИИ:")
        
        # Форматируем данные для LLM с темами
        analysis_text = f"""
АНАЛИЗ ДИАЛОГА: {disc_results['dialog_title']}

ПСИХОЛОГИЧЕСКИЕ СТИЛИ:
{disc_results['disc_results']}

ТЕМЫ РАЗГОВОРА:
{topic_results['dominant_topics']}

ИНТЕРЕСЫ УЧАСТНИКОВ:
{topic_results['participant_interests']}

СФОРМУЛИРУЙ РЕКОМЕНДАЦИИ:
"""
        
        try:
            advice = self.psych_advisor.get_recommendations(
                disc_results['disc_results'],
                disc_results['dialog_title']
            )
            print(advice)
        except Exception as e:
            print(f"   Рекомендации временно недоступны: {e}")
            print("    Попробуйте запустить позже, когда модель загрузится")
        
        print(f"\n{'='*60}")
        print("АНАЛИЗ ЗАВЕРШЁН")
        print('='*60)
        
        return {
            'disc_analysis': disc_results,
            'topic_analysis': topic_results
        }

# ЗАПУСК
if __name__ == "__main__":
    analyzer = UnifiedAnalyzer()
    
    # Тестируем на первом диалоге
    test_file = "backend/dialogs/1.json"
    
    if os.path.exists(test_file):
        analyzer.analyze_dialog(test_file)
    else:
        print(f"Файл {test_file} не найден!")
        print("Доступные файлы:")
        for root, dirs, files in os.walk("backend"):
            for file in files:
                if file.endswith('.json'):
                    print(f"  - {os.path.join(root, file)}")