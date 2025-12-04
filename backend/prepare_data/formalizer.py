import json
import os
import sys
from typing import Any, List, Dict

def extract_text_from_entities(text_field: Any) -> str:
    """
    Извлекает текст из поля 'text', которое может быть:
    - строкой (обычное сообщение)
    - списком словарей (сообщение с ссылками, упоминаниями и т.д.)
    - пустым списком или пустой строкой
    """
    if isinstance(text_field, str):
        return text_field.strip()
    elif isinstance(text_field, list):
        # Собираем все текстовые части
        parts = []
        for item in text_field:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"].strip())
        return " ".join(parts).strip()
    else:
        return ""

def clean_telegram_export(input_path: str, output_path: str):
    """
    Преобразует экспорт Telegram в формат, совместимый с MainAnalyzer.
    
    Ожидаемый вход: result.json от Telegram Desktop
    Выход: cleaned_chat.json с минимальной структурой
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Базовые метаданные
    cleaned = {
        "dialog_id": data.get("id"),
        "title": data.get("name"),
        "messages": []
    }

    for msg in data.get("messages", []):
        # Пропускаем не-сообщения (service-сообщения и т.п.)
        if msg.get("type") != "message":
            continue

        # Извлекаем текст (обрабатываем разные форматы)
        raw_text = msg.get("text", "")
        text = extract_text_from_entities(raw_text)

        # Пропускаем пустые сообщения и медиа без текста
        if not text:
            continue

        # Сохраняем только нужные поля
        cleaned_msg = {
            "sender": msg.get("from", "Unknown"),
            "text": text,
            "time": msg.get("date")  # ISO 8601, подходит для большинства целей
        }
        cleaned["messages"].append(cleaned_msg)

    # Сохраняем результат
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"✅ Успешно обработано {len(cleaned['messages'])} сообщений.")
    print(f"📁 Результат сохранён в: {output_path}")

if __name__ == "__main__":
    input_file = input()
    if not os.path.exists(input_file):
        print(f"❌ Файл не найден: {input_file}")
        sys.exit(1)

    output_file = "/home/fedosdan2/prog/pr_act/PROJECT/analysis_results/cleaned_chat.json"
    clean_telegram_export(input_file, output_file)