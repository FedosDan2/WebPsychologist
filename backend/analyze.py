from transformers import pipeline
import json
import os
import re
import statistics
from collections import defaultdict
from topic_analyze import extract_topics_from_dialog  # твоя LLM-функция

# ✅ Эмоции
emotion_model = pipeline(
    "text-classification",
    model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
    return_all_scores=True,
    top_k=None
)

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'[^\w\s.,!?а-яА-ЯёЁ]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text or ""

def get_emotion(text):
    preds = emotion_model(text)[0]
    result = {"negative": 0.0, "neutral": 0.0, "positive": 0.0}
    for p in preds:
        label = p["label"].lower()
        if "neg" in label:
            result["negative"] = round(p["score"], 3)
        elif "neu" in label:
            result["neutral"] = round(p["score"], 3)
        elif "pos" in label:
            result["positive"] = round(p["score"], 3)
    return result

def analyze_participant(sender, messages):
    cleaned_messages = []
    texts = []

    for msg in messages:
        raw_text = msg.get("text")
        if not raw_text:
            continue
        clean = clean_text(raw_text)
        if not clean:
            continue
        cleaned_messages.append((msg, clean))
        texts.append(clean)

    if not texts:
        return {
            "messages_count": 0,
            "emotions_median": {"negative": 0.0, "neutral": 0.0, "positive": 0.0},
            "topics": [],
            "messages": []
        }

    # Анализ эмоций
    emotions_total = defaultdict(list)
    messages_out = []

    for orig_msg, clean_txt in cleaned_messages:
        e = get_emotion(clean_txt)
        for k, v in e.items():
            emotions_total[k].append(v)
        messages_out.append({
            "text": orig_msg["text"],
            "time": orig_msg.get("time"),
            "emotion_scores": e
        })

    emotions_median = {k: round(statistics.median(vs), 3) for k, vs in emotions_total.items()}
    for k in ["negative", "neutral", "positive"]:
        emotions_median.setdefault(k, 0.0)

    # 🔥 Получаем темы через LLM (только по текстам этого участника)
    try:
        participant_topics = extract_topics_from_dialog(messages)
    except Exception as e:
        print(f"⚠️ Ошибка LLM для {sender}: {e}")
        participant_topics = ["ошибка_темы"]

    return {
        "messages_count": len(messages_out),
        "emotions_median": emotions_median,
        "topics": participant_topics,  # ← список строк
        "messages": messages_out
    }

def analyze_dialog_by_participant(dialog_path):
    try:
        with open(dialog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"error": f"Ошибка чтения файла {dialog_path}: {e}"}

    messages = data.get("messages", [])
    if not messages:
        return {"dialog_id": data.get("dialog_id") or data.get("id"), "error": "Пустой диалог"}

    # Группируем по отправителям
    grouped = {}
    for msg in messages:
        sender = msg.get("sender")
        if sender:
            grouped.setdefault(sender, []).append(msg)

    participants_data = {}
    for sender, msgs in grouped.items():
        try:
            participants_data[sender] = analyze_participant(sender, msgs)
        except Exception as e:
            participants_data[sender] = {"error": str(e)}

    # 🔥 Темы для ВСЕГО диалога (опционально)
    try:
        dialog_topics = extract_topics_from_dialog(messages)
    except Exception as e:
        print(f"⚠️ Ошибка LLM на всём диалоге: {e}")
        dialog_topics = ["ошибка_темы"]

    return {
        "dialog_id": data.get("dialog_id") or data.get("id"),
        "title": data.get("title"),
        "dialog_topics": dialog_topics,           # темы всего диалога
        "participants_analysis": participants_data
    }

def main():
    out_dir = "/home/fedosdan2/prog/pr_act/PROJECT/backend/analysis_results"
    os.makedirs(out_dir, exist_ok=True)

    fpath = "/home/fedosdan2/prog/pr_act/PROJECT/backend/dialogs/2.json"
    f = os.path.basename(fpath)
    res = analyze_dialog_by_participant(fpath)
    out_path = os.path.join(out_dir, f"{os.path.splitext(f)[0]}_analysis.json")
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump(res, out, indent=2, ensure_ascii=False)

    print(f"✅ {f} → сохранён в {out_path}")

if __name__ == "__main__":
    main()