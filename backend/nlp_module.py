import json, os, re, torch
from deep_translator import GoogleTranslator
from nltk.sentiment import SentimentIntensityAnalyzer
from concurrent.futures import ThreadPoolExecutor, as_completed
from transformers import pipeline

emotion_model = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", return_all_scores=True)

def get_emotion(text_en):
    preds = emotion_model(text_en)[0]
    return {p["label"]: round(p["score"], 3) for p in preds}

# Инициализация
sia = SentimentIntensityAnalyzer()
num_workers = min(os.cpu_count() * 2, 12)  # ограничим, чтобы не словить 429 от Google


def clean_text(text: str) -> str:
    """Очистка текста от лишних символов"""
    text = re.sub(r'[^\w\s.,!?а-яА-ЯёЁ]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def batch_translate_texts(texts):
    """Переводит список сообщений одним запросом"""
    if not texts:
        return []
    try:
        joined = " ||| ".join(texts)
        translated = GoogleTranslator(source='auto', target='en').translate(joined)
        return [t.strip() for t in translated.split("|||")]
    except Exception:
        # если GoogleTranslator вернул ошибку, возвращаем исходный текст
        return texts


def analyze_participant(sender, messages):
    texts = [clean_text(m["text"]) for m in messages if m.get("text")]
    translated_texts = batch_translate_texts(texts)

    emotions_total = {}  # динамически
    scores = []
    messages_out = []

    for orig, trans in zip(messages, translated_texts):
        e = get_emotion(trans)
        s = sia.polarity_scores(trans)
        for k, v in e.items():
            emotions_total[k] = emotions_total.get(k, 0.0) + v
        scores.append(s)
        messages_out.append({
            "text": orig["text"],
            "time": orig.get("time"),
            "emotion_scores": e,
            "sentiment": s
        })

    if scores:
        avg_sent = {
            "neg": sum(s["neg"] for s in scores) / len(scores),
            "neu": sum(s["neu"] for s in scores) / len(scores),
            "pos": sum(s["pos"] for s in scores) / len(scores),
            "compound": sum(s["compound"] for s in scores) / len(scores)
        }
    else:
        avg_sent = {"neg": 0, "neu": 0, "pos": 0, "compound": 0}

    return {
        "messages_count": len(messages_out),
        "emotions_total": emotions_total,
        "avg_sentiment": avg_sent,
        "messages": messages_out
    }



def analyze_dialog_by_participant(dialog_path):
    """Главная функция анализа диалога"""
    try:
        with open(dialog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"error": f"Ошибка чтения файла {dialog_path}: {e}"}

    messages = data.get("messages", [])
    if not messages:
        return {"dialog_id": data.get("id"), "error": "Пустой диалог"}

    # группируем сообщения по участникам
    grouped = {}
    for msg in messages:
        sender = msg.get("sender")
        if not sender:
            continue
        grouped.setdefault(sender, []).append(msg)

    participants_data = {}

    # ⚡ параллельная обработка участников
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(analyze_participant, s, m): s for s, m in grouped.items()}
        for future in as_completed(futures):
            sender = futures[future]
            try:
                participants_data[sender] = future.result()
            except Exception as e:
                participants_data[sender] = {"error": str(e)}

    return {
        "dialog_id": data.get("dialog_id"),
        "title": data.get("title"),
        "participants_analysis": participants_data
    }


def main():
    dialog_dir = "/home/fedosdan2/prog/pr_act/PROJECT/backend/dialogs"
    for f in os.listdir(dialog_dir):
        if f.endswith(".json"):
            fpath = os.path.join(dialog_dir, f)
            res = analyze_dialog_by_participant(fpath)
            print(f"\n📁 {os.path.basename(f)}")
            print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
