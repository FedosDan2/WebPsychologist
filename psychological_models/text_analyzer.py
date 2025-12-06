def analyze_text_for_disc(text):
    """
    Анализирует текст и определяет DISC-профиль
    На основе ключевых слов и паттернов
    """
    text = text.lower()
    
    scores = {"D": 0, "I": 0, "S": 0, "C": 0}
    
    # Ключевые слова для каждого типа
    d_keywords = ["срочно", "результат", "контроль", "решаю", "быстро", "успех"]
    i_keywords = ["отлично", "супер", "круто", "😊", "!", "вместе", "команда"]
    s_keywords = ["спокойно", "помощь", "поддержка", "стабильность", "доверие"]
    c_keywords = ["анализ", "данные", "детали", "проверить", "точность", "?"]
    
    # Считаем совпадения
    for word in d_keywords:
        if word in text:
            scores["D"] += 1
    
    for word in i_keywords:
        if word in text:
            scores["I"] += 1
            # Эмодзи и восклицания дают бонус для I
        if "!" in text:
            scores["I"] += text.count("!") * 0.5
        if "😊" in text or "😂" in text:
            scores["I"] += 2
    
    for word in s_keywords:
        if word in text:
            scores["S"] += 1
    
    for word in c_keywords:
        if word in text:
            scores["C"] += 1
        # Вопросы дают бонус для C
        if "?" in text:
            scores["C"] += text.count("?") * 0.5
    
    return scores

def compare_profiles(self_assessment, actual_behavior):
    """Сравнивает самооценку и реальное поведение"""
    discrepancy = {}
    
    for style in ["D", "I", "S", "C"]:
        diff = actual_behavior[style] - self_assessment[style]
        discrepancy[style] = diff
    
    return discrepancy


if __name__ == "__main__":
    # Пример переписки
    test_text = """
    Привет! Как дела? 😊 
    Мне нужно чтобы ты проверил все данные по проекту. 
    Очень важно сделать это точно и без ошибок!
    """
    
    print("=== АНАЛИЗ ТЕКСТА ===")
    print(f"Текст: {test_text}")
    
    text_profile = analyze_text_for_disc(test_text)
    print(f"DISC профиль текста: {text_profile}")
    
    # Пример сравнения с самооценкой
    self_profile = {"D": 2, "I": 3, "S": 1, "C": 4}  # Например, из опросника
    
    comparison = compare_profiles(self_profile, text_profile)
    print(f"Различия: {comparison}")