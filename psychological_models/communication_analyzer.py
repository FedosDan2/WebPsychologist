import json
import os
from datetime import datetime
from collections import Counter
import re

class CommunicationAnalyzer:
    """Анализирует все 6 аспектов коммуникации из твоего задания"""
    
    def __init__(self):
        # Словари для анализа эмоций
        self.positive_words = [
            "спасибо", "отлично", "хорошо", "супер", "прекрасно", 
            "замечательно", "восхитительно", "молодец", "умница", 
            "браво", "класс", "круто", "здорово", "великолепно",
            "👍", "😊", "❤️", "😂", "🎉", "👏", "🤗"
        ]
        
        self.negative_words = [
            "проблема", "сложно", "трудно", "не могу", "устал", 
            "плохо", "ужасно", "кошмар", "беда", "катастрофа",
            "разочарован", "обидно", "грустно", "печально",
            "😔", "😠", "😡", "😭", "💔", "👎"
        ]
        
        # Паттерны инициативы
        self.initiative_patterns = [
            "давай обсудим", "предлагаю", "хочу сказать", "у меня идея",
            "как насчёт", "может быть", "что если", "я думаю"
        ]
    
    # ============================================
    # 1. ЧАСТОТА СООБЩЕНИЙ
    # ============================================
    
    def analyze_message_frequency(self, messages, participants):
        """
        Анализирует частоту сообщений каждого участника
        
        Возвращает:
        - total_messages: общее количество сообщений
        - message_percentage: процент от всех сообщений  
        - avg_length: средняя длина сообщения
        - response_speed: среднее время ответа (если есть время)
        """
        frequency_stats = {}
        total_messages = len(messages)
        
        for participant in participants:
            participant_messages = [m for m in messages if m['sender'] == participant]
            message_count = len(participant_messages)
            
            # Средняя длина сообщения
            total_length = sum(len(m['text']) for m in participant_messages)
            avg_length = total_length / message_count if message_count > 0 else 0
            
            frequency_stats[participant] = {
                'total_messages': message_count,
                'message_percentage': (message_count / total_messages * 100) if total_messages > 0 else 0,
                'avg_message_length': round(avg_length, 1),
                'messages_per_hour': self.calculate_messages_per_hour(participant_messages),
                'is_most_active': False  # заполним позже
            }
        
        # Определяем самого активного
        if frequency_stats:
            most_active = max(frequency_stats.items(), key=lambda x: x[1]['total_messages'])
            frequency_stats[most_active[0]]['is_most_active'] = True
        
        return frequency_stats
    
    def calculate_messages_per_hour(self, messages):
        """Считает среднее количество сообщений в час"""
        if len(messages) < 2:
            return 0
        
        # Если есть время в сообщениях
        try:
            times = []
            for msg in messages:
                if 'time' in msg:
                    time_str = msg['time']
                    # Пробуем разные форматы времени
                    try:
                        t = datetime.strptime(time_str, "%H:%M")
                        times.append(t)
                    except:
                        pass
            
            if len(times) >= 2:
                time_diff = (max(times) - min(times)).total_seconds() / 3600
                if time_diff > 0:
                    return len(messages) / time_diff
        except:
            pass
        
        return 0
    
    # ============================================
    # 2. БАЛАНС ИНИЦИАТИВЫ
    # ============================================
    
    def analyze_initiative_balance(self, messages, participants):
        """
        Анализирует кто чаще проявляет инициативу
        
        Метрики:
        - starts_conversation: начинает новые цепочки
        - asks_questions: задаёт вопросы
        - uses_initiative_patterns: использует инициативные фразы
        - initiative_score: общий балл инициативности
        """
        initiative_stats = {p: {
            'starts_conversation': 0,
            'asks_questions': 0,
            'uses_initiative_patterns': 0,
            'initiative_score': 0
        } for p in participants}
        
        # Анализируем каждое сообщение
        for i, message in enumerate(messages):
            sender = message['sender']
            text = message['text'].lower()
            
            # 1. Начинает ли разговор (первое сообщение или после паузы)
            if i == 0 or messages[i-1]['sender'] != sender:
                initiative_stats[sender]['starts_conversation'] += 1
            
            # 2. Задаёт ли вопросы
            if '?' in text:
                initiative_stats[sender]['asks_questions'] += 1
            
            # 3. Использует ли инициативные паттерны
            if any(pattern in text for pattern in self.initiative_patterns):
                initiative_stats[sender]['uses_initiative_patterns'] += 1
        
        # Считаем общий балл
        for participant in participants:
            stats = initiative_stats[participant]
            stats['initiative_score'] = (
                stats['starts_conversation'] * 3 +  # Начать разговор = +3
                stats['asks_questions'] * 2 +       # Задать вопрос = +2
                stats['uses_initiative_patterns'] * 2  # Инициативная фраза = +2
            )
        
        return initiative_stats
    
    # ============================================
    # 3. ДОЛЯ ПОЛОЖИТЕЛЬНЫХ/НЕГАТИВНЫХ ФРАЗ
    # ============================================
    
    def analyze_sentiment_balance(self, messages, participants):
        """
        Анализирует эмоциональную окраску сообщений
        
        Возвращает:
        - positive_count: количество позитивных сообщений
        - negative_count: количество негативных сообщений  
        - neutral_count: количество нейтральных сообщений
        - sentiment_ratio: отношение позитивных к негативным
        - dominant_sentiment: преобладающая эмоция
        """
        sentiment_stats = {}
        
        for participant in participants:
            participant_messages = [m for m in messages if m['sender'] == participant]
            
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for msg in participant_messages:
                text = msg['text'].lower()
                
                # Проверяем на позитивные слова
                is_positive = any(word in text for word in self.positive_words)
                # Проверяем на негативные слова
                is_negative = any(word in text for word in self.negative_words)
                
                # Эмодзи тоже учитываем
                positive_emojis = ["😊", "❤️", "😂", "🎉", "👍", "👏", "🤗"]
                negative_emojis = ["😔", "😠", "😡", "😭", "💔", "👎"]
                
                for emoji in positive_emojis:
                    if emoji in text:
                        is_positive = True
                
                for emoji in negative_emojis:
                    if emoji in text:
                        is_negative = True
                
                # Классифицируем сообщение
                if is_positive and not is_negative:
                    positive_count += 1
                elif is_negative and not is_positive:
                    negative_count += 1
                elif is_positive and is_negative:
                    # Смешанное сообщение
                    positive_count += 0.5
                    negative_count += 0.5
                else:
                    neutral_count += 1
            
            total = len(participant_messages)
            
            # Определяем доминирующую эмоцию
            if positive_count > negative_count and positive_count > neutral_count:
                dominant_sentiment = "positive"
            elif negative_count > positive_count and negative_count > neutral_count:
                dominant_sentiment = "negative"
            else:
                dominant_sentiment = "neutral"
            
            sentiment_stats[participant] = {
                'positive_count': round(positive_count, 1),
                'negative_count': round(negative_count, 1),
                'neutral_count': round(neutral_count, 1),
                'positive_percentage': (positive_count / total * 100) if total > 0 else 0,
                'negative_percentage': (negative_count / total * 100) if total > 0 else 0,
                'neutral_percentage': (neutral_count / total * 100) if total > 0 else 0,
                'sentiment_ratio': positive_count / negative_count if negative_count > 0 else float('inf'),
                'dominant_sentiment': dominant_sentiment,
                'emotional_balance': self.get_emotional_balance_label(
                    positive_count, negative_count, total
                )
            }
        
        return sentiment_stats
    
    def get_emotional_balance_label(self, positive, negative, total):
        """Определяет метку эмоционального баланса"""
        if total == 0:
            return "нет данных"
        
        pos_ratio = positive / total
        neg_ratio = negative / total
        
        if pos_ratio > 0.6:
            return "очень позитивный"
        elif pos_ratio > 0.4:
            return "позитивный"
        elif neg_ratio > 0.6:
            return "очень негативный"
        elif neg_ratio > 0.4:
            return "негативный"
        elif abs(pos_ratio - neg_ratio) < 0.1:
            return "сбалансированный"
        else:
            return "нейтральный"
    
    # ============================================
    # 4. СИЛЬНЫЕ СТОРОНЫ ОБЩЕНИЯ
    # ============================================
    
    def identify_communication_strengths(self, disc_results, frequency_stats, 
                                        sentiment_stats, initiative_stats):
        """
        Определяет сильные стороны каждого участника
        
        Сильные стороны могут быть:
        - По DISC стилю
        - По активности (частота сообщений)
        - По эмоциям (позитивность)
        - По инициативе
        - По балансу (если всё сбалансировано)
        """
        strengths = {}
        
        for participant in disc_results.keys():
            participant_strengths = []
            
            # Сильные стороны по DISC стилю
            if participant in disc_results:
                disc_data = disc_results[participant]
                disc_style = disc_data.get('dominant_style', '')
                
                disc_strengths = {
                    'D': ["Решительность", "Ориентация на результат", "Лидерские качества"],
                    'I': ["Эмпатия", "Умение мотивировать", "Коммуникабельность"],
                    'S': ["Надёжность", "Поддержка", "Стабильность"],
                    'C': ["Аналитичность", "Точность", "Системность"]
                }
                
                if disc_style in disc_strengths:
                    participant_strengths.extend(disc_strengths[disc_style])
            
            # Сильные стороны по активности
            if participant in frequency_stats:
                freq_data = frequency_stats[participant]
                
                if freq_data.get('is_most_active', False):
                    participant_strengths.append("Активное участие в общении")
                
                if freq_data.get('message_percentage', 0) > 60:
                    participant_strengths.append("Ведёт диалог")
                elif 40 <= freq_data.get('message_percentage', 0) <= 60:
                    participant_strengths.append("Сбалансированное участие")
            
            # Сильные стороны по эмоциям
            if participant in sentiment_stats:
                sent_data = sentiment_stats[participant]
                
                if sent_data.get('dominant_sentiment') == 'positive':
                    participant_strengths.append("Позитивный настрой")
                
                if sent_data.get('positive_percentage', 0) > 70:
                    participant_strengths.append("Создаёт позитивную атмосферу")
                
                if sent_data.get('emotional_balance') == 'сбалансированный':
                    participant_strengths.append("Эмоциональная сбалансированность")
            
            # Сильные стороны по инициативе
            if participant in initiative_stats:
                init_data = initiative_stats[participant]
                
                if init_data.get('initiative_score', 0) > 5:
                    participant_strengths.append("Проявляет инициативу")
                
                if init_data.get('asks_questions', 0) > 3:
                    participant_strengths.append("Активное слушание (задаёт вопросы)")
            
            # Убираем дубликаты
            strengths[participant] = list(set(participant_strengths))
        
        return strengths
    
    # ============================================
    # 5. ПОТЕНЦИАЛЬНЫЕ РИСКИ
    # ============================================
    
    def identify_communication_risks(self, disc_results, frequency_stats,
                                    sentiment_stats, initiative_stats):
        """
        Определяет потенциальные проблемы в общении
        
        Риски могут быть:
        - По DISC стилю (крайние проявления)
        - По активности (слишком много/мало)
        - По эмоциям (излишний негатив/позитив)
        - По инициативе (нет инициативы/слишком много)
        - По балансу (дисбаланс в диалоге)
        """
        risks = {}
        
        for participant in disc_results.keys():
            participant_risks = []
            
            # Риски по DISC стилю
            if participant in disc_results:
                disc_data = disc_results[participant]
                disc_style = disc_data.get('dominant_style', '')
                disc_percentages = disc_data.get('percentages', {})
                
                # D-стиль риски
                if disc_style == 'D' and disc_percentages.get('D', 0) > 70:
                    participant_risks.append("Риск агрессивного или диктаторского поведения")
                    participant_risks.append("Может подавлять мнение других")
                
                # S-стиль риски
                if disc_style == 'S' and disc_percentages.get('S', 0) > 70:
                    participant_risks.append("Риск пассивности и избегания конфликтов")
                    participant_risks.append("Может не проявлять инициативу")
                
                # C-стиль риски
                if disc_style == 'C' and disc_percentages.get('C', 0) > 70:
                    participant_risks.append("Риск излишней детализации и занудства")
                    participant_risks.append("Может медлить с решениями")
            
            # Риски по активности
            if participant in frequency_stats:
                freq_data = frequency_stats[participant]
                
                if freq_data.get('message_percentage', 0) > 80:
                    participant_risks.append("Доминирует в разговоре, не даёт высказаться")
                elif freq_data.get('message_percentage', 0) < 20:
                    participant_risks.append("Слишком мало участвует в общении")
            
            # Риски по эмоциям
            if participant in sentiment_stats:
                sent_data = sentiment_stats[participant]
                
                if sent_data.get('negative_percentage', 0) > 50:
                    participant_risks.append("Высокий уровень негатива в общении")
                    participant_risks.append("Может создавать напряжённую атмосферу")
                
                if sent_data.get('positive_percentage', 0) > 90:
                    participant_risks.append("Возможна поверхностность (излишний позитив)")
            
            # Риски по инициативе
            if participant in initiative_stats:
                init_data = initiative_stats[participant]
                
                if init_data.get('initiative_score', 0) == 0:
                    participant_risks.append("Отсутствие инициативы, только реакция")
                elif init_data.get('initiative_score', 0) > 10:
                    participant_risks.append("Может перетягивать внимание на себя")
            
            # Риски по балансу с другими участниками
            participant_risks.extend(
                self.identify_relationship_risks(participant, disc_results, frequency_stats)
            )
            
            risks[participant] = participant_risks
        
        return risks
    
    def identify_relationship_risks(self, participant, disc_results, frequency_stats):
        """Определяет риски во взаимоотношениях с другими участниками"""
        relationship_risks = []
        other_participants = [p for p in disc_results.keys() if p != participant]
        
        for other in other_participants:
            # Риски по совместимости DISC стилей
            my_style = disc_results[participant].get('dominant_style', '')
            other_style = disc_results[other].get('dominant_style', '')
            
            # D vs S/C - риск давления
            if my_style == 'D' and other_style in ['S', 'C']:
                relationship_risks.append(f"Может оказывать давление на {other} (S/C-тип)")
            
            # I vs C - риск поверхностности
            if my_style == 'I' and other_style == 'C':
                relationship_risks.append(f"Может казаться поверхностным для {other} (C-тип)")
        
        return relationship_risks
    
    # ============================================
    # 6. СРАВНЕНИЕ САМООЦЕНКИ И ВОСПРИЯТИЯ
    # ============================================
    
    def compare_self_assessment_vs_reality(self, self_assessment, actual_behavior,
                                          frequency_stats, sentiment_stats):
        """
        Сравнивает как человек себя видит vs как его видят другие
        
        self_assessment: словарь с самооценкой пользователя
        actual_behavior: результаты анализа его реального поведения
        """
        discrepancies = {}
        
        for participant, self_data in self_assessment.items():
            if participant not in actual_behavior:
                continue
            
            actual_data = actual_behavior[participant]
            
            # Сравнение DISC стилей
            self_style = self_data.get('disc_style', '').upper()
            actual_style = actual_data.get('dominant_style', '')
            
            style_match = self_style == actual_style
            
            # Сравнение эмоциональной самооценки
            self_emotional = self_data.get('emotional_type', '')
            actual_emotional = sentiment_stats.get(participant, {}).get('dominant_sentiment', '')
            
            emotional_match = self_emotional == actual_emotional
            
            # Сравнение активности
            self_active = self_data.get('communication_style', '')
            actual_percentage = frequency_stats.get(participant, {}).get('message_percentage', 0)
            
            if 'активн' in self_active.lower() and actual_percentage < 30:
                activity_match = False
            elif 'спокойн' in self_active.lower() and actual_percentage > 70:
                activity_match = False
            else:
                activity_match = True
            
            # Генерация инсайтов
            insights = []
            
            if not style_match and self_style and actual_style:
                style_names = {
                    'D': 'решительный лидер',
                    'I': 'общительный мотиватор',
                    'S': 'спокойный поддерживающий',
                    'C': 'аналитичный системный'
                }
                insights.append(
                    f"Вы считаете себя {style_names.get(self_style, self_style.lower())}, "
                    f"но в общении проявляетесь как {style_names.get(actual_style, actual_style.lower())}. "
                    f"Это может означать адаптацию к ситуации или слепую зону в самовосприятии."
                )
            
            if not emotional_match and self_emotional and actual_emotional:
                emotional_names = {
                    'positive': 'позитивным',
                    'negative': 'негативным', 
                    'neutral': 'нейтральным'
                }
                insights.append(
                    f"Вы воспринимаете себя как {emotional_names.get(self_emotional, self_emotional.lower())}, "
                    f"но ваши сообщения чаще {emotional_names.get(actual_emotional, actual_emotional.lower())}. "
                    f"Возможно, вы не осознаёте как звучат ваши слова для других."
                )
            
            discrepancies[participant] = {
                'style_match': style_match,
                'emotional_match': emotional_match,
                'activity_match': activity_match,
                'self_assessment': self_data,
                'actual_behavior': {
                    'disc_style': actual_style,
                    'emotional_type': actual_emotional,
                    'activity_level': self.get_activity_level_label(actual_percentage)
                },
                'insights': insights,
                'match_score': self.calculate_match_score(style_match, emotional_match, activity_match)
            }
        
        return discrepancies
    
    def get_activity_level_label(self, percentage):
        """Определяет метку уровня активности"""
        if percentage > 70:
            return "очень активный"
        elif percentage > 50:
            return "активный"
        elif percentage > 30:
            return "умеренный"
        else:
            return "спокойный"
    
    def calculate_match_score(self, style_match, emotional_match, activity_match):
        """Считает общий балл совпадения самооценки и реальности"""
        score = 0
        if style_match:
            score += 40
        if emotional_match:
            score += 30
        if activity_match:
            score += 30
        return score
    
    # ============================================
    # ГЛАВНЫЙ МЕТОД - ВЫЗЫВАЕТ ВСЕ 6 АНАЛИЗОВ
    # ============================================
    
    def analyze_all_aspects(self, messages, participants, disc_results=None, 
                           self_assessment=None, dialog_title=""):
        """
        Главный метод: выполняет все 6 анализов и возвращает полный отчёт
        
        Параметры:
        - messages: список сообщений диалога
        - participants: список участников
        - disc_results: результаты DISC анализа (если есть)
        - self_assessment: данные самооценки (если есть)
        - dialog_title: название диалога
        """
        
        print(f"\n ПОЛНЫЙ АНАЛИЗ КОММУНИКАЦИИ: {dialog_title}")
        print("=" * 60)
        
        # Если нет disc_results, создаём заглушку
        if not disc_results:
            disc_results = {p: {'dominant_style': 'S', 'percentages': {}} for p in participants}
        
        # 1. Частота сообщений
        print("\n1️ ЧАСТОТА СООБЩЕНИЙ:")
        frequency_stats = self.analyze_message_frequency(messages, participants)
        for participant, stats in frequency_stats.items():
            print(f"    {participant}: {stats['total_messages']} сообщений "
                  f"({stats['message_percentage']:.1f}%)")
            if stats.get('is_most_active'):
                print(f"      Самый активный участник")
        
        # 2. Баланс инициативы
        print("\n2️ БАЛАНС ИНИЦИАТИВЫ:")
        initiative_stats = self.analyze_initiative_balance(messages, participants)
        for participant, stats in initiative_stats.items():
            print(f"    {participant}: балл инициативы {stats['initiative_score']}")
            if stats['initiative_score'] > 5:
                print(f"      Проявляет хорошую инициативу")
        
        # 3. Эмоциональный баланс
        print("\n3️ ЭМОЦИОНАЛЬНЫЙ БАЛАНС:")
        sentiment_stats = self.analyze_sentiment_balance(messages, participants)
        for participant, stats in sentiment_stats.items():
            print(f"   👤 {participant}: {stats['dominant_sentiment']} "
                  f"({stats['positive_percentage']:.1f}% позитивных)")
        
        # 4. Сильные стороны
        print("\n4️ СИЛЬНЫЕ СТОРОНЫ ОБЩЕНИЯ:")
        strengths = self.identify_communication_strengths(
            disc_results, frequency_stats, sentiment_stats, initiative_stats
        )
        for participant, strength_list in strengths.items():
            if strength_list:
                print(f"    {participant}:")
                for strength in strength_list[:3]:  # Показываем первые 3
                    print(f"      {strength}")
        
        # 5. Потенциальные риски
        print("\n5️ ПОТЕНЦИАЛЬНЫЕ РИСКИ:")
        risks = self.identify_communication_risks(
            disc_results, frequency_stats, sentiment_stats, initiative_stats
        )
        for participant, risk_list in risks.items():
            if risk_list:
                print(f"    {participant}:")
                for risk in risk_list[:2]:  # Показываем первые 2 риска
                    print(f"       {risk}")
        
        # 6. Сравнение самооценки и реальности (если есть данные)
        if self_assessment:
            print("\n6️ СРАВНЕНИЕ САМООЦЕНКИ И РЕАЛЬНОСТИ:")
            comparison = self.compare_self_assessment_vs_reality(
                self_assessment, disc_results, frequency_stats, sentiment_stats
            )
            for participant, data in comparison.items():
                print(f"    {participant}: совпадение {data['match_score']}%")
                for insight in data.get('insights', [])[:2]:
                    print(f"      {insight}")
        
        # Собираем все результаты в один словарь
        all_results = {
            'dialog_title': dialog_title,
            'frequency_analysis': frequency_stats,
            'initiative_analysis': initiative_stats,
            'sentiment_analysis': sentiment_stats,
            'strengths_analysis': strengths,
            'risks_analysis': risks,
            'participants': participants,
            'total_messages': len(messages)
        }
        
        if self_assessment:
            all_results['self_assessment_comparison'] = comparison
        
        print("\n" + "=" * 60)
        print(" АНАЛИЗ ЗАВЕРШЁН")
        print("=" * 60)
        
        return all_results

# ============================================
# ТЕСТИРОВАНИЕ
# ============================================

# if __name__ == "__main__":
#     # Тестовые данные
#     test_messages = [
#         {"sender": "Алексей", "text": "Доброе утро, Ирина. Напомни, презентация готова?"},
#         {"sender": "Ирина", "text": "Доброе! Почти, осталось диаграммы дооформить."},
#         {"sender": "Алексей", "text": "Мы должны были отправить вчера. Это проблема."},
#         {"sender": "Ирина", "text": "Да, извините. Возникли трудности с отчётом."},
#         {"sender": "Алексей", "text": "Ладно, помогу. Вместе решим."},
#         {"sender": "Ирина", "text": "Спасибо за поддержку! Вы лучший 😊"},
#         {"sender": "Алексей", "text": "Отчёт хороший, кстати. Видно, что ты вникаешь."},
#         {"sender": "Ирина", "text": "Рада, что понравилось!"}
#     ]
    
#     test_participants = ["Алексей", "Ирина"]
    
#     # Тестовые DISC результаты
#     test_disc_results = {
#         "Алексей": {
#             "dominant_style": "D",
#             "percentages": {"D": 60, "I": 20, "S": 10, "C": 10}
#         },
#         "Ирина": {
#             "dominant_style": "S", 
#             "percentages": {"D": 10, "I": 30, "S": 50, "C": 10}
#         }
#     }
    
#     # Тестовая самооценка
#     test_self_assessment = {
#         "Алексей": {
#             "disc_style": "C",  # Думает, что он аналитик
#             "emotional_type": "neutral",
#             "communication_style": "спокойный"
#         },
#         "Ирина": {
#             "disc_style": "I",  # Думает, что она общительная
#             "emotional_type": "positive", 
#             "communication_style": "активный"
#         }
#     }
    
#     # Запускаем анализ
#     analyzer = CommunicationAnalyzer()
    
#     results = analyzer.analyze_all_aspects(
#         messages=test_messages,
#         participants=test_participants,
#         disc_results=test_disc_results,
#         self_assessment=test_self_assessment,
#         dialog_title="Тестовый диалог: Начальник и сотрудница"
#     )
    
#     # Сохраняем результаты
#     output_file = "communication_analysis_results.json"
#     with open(output_file, 'w', encoding='utf-8') as f:
#         json.dump(results, f, ensure_ascii=False, indent=2)
    
#     print(f"\n📁 Результаты сохранены в: {output_file}")