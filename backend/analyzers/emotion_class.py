from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import json, os, re, statistics
from collections import defaultdict
from analyzers.disc_class import DISCAnalyze
from analyzers.topic_class import TopicAnalyzer


from transformers import (
    XLMRobertaTokenizer,
    XLMRobertaForSequenceClassification,
    pipeline
)

print("📥 Загружаем модель эмоций...")
model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

# Явно используем slow-токенизатор без конвертации
tokenizer = XLMRobertaTokenizer.from_pretrained(model_name, use_fast=False)
model = XLMRobertaForSequenceClassification.from_pretrained(model_name)

emotion_model = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    return_all_scores=True,
    top_k=None
)

class MainAnalyzer():
    def __init__(self):
        self.dominant_emotion = None
        self.sender_clean_text = {}
        self.sender_disc_analyze = {}

        self.type_descriptions = {
            "D": "Решительный, ориентированный на результат",
            "I": "Общительный, эмоциональный, вдохновляющий", 
            "S": "Стабильный, надежный, спокойный",
            "C": "Аналитичный, точный, системный"
        }

    def _clean_text(self, text):
        if not isinstance(text, str):
            return ""
        text = re.sub(r'[^\w\s.,!?а-яА-ЯёЁ]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.lower()
        return text or ""


    # --------------------- EMOTIONS ---------------------------
    def _get_emotion(self, text):
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


    def _emotions_analyze(self, data):
        batch_size = 50

        def analyze_participant(sender, messages):
            # Группируем сообщения по батчам
            batches = [messages[i:i + batch_size] for i in range(0, len(messages), batch_size)]

            # Объединяем результаты по всем батчам
            all_emotions = defaultdict(list)
            total_messages_count = 0
            all_messages_out = []

            for batch in batches:
                cleaned_messages = []
                texts = []

                for msg in batch:
                    raw_text = msg.get("text")
                    if not raw_text:
                        continue
                    clean = self._clean_text(raw_text)
                    if not clean:
                        continue
                    cleaned_messages.append((msg, clean))
                    texts.append(clean)

                if not texts:
                    continue

                # Анализ эмоций для батча
                for orig_msg, clean_txt in cleaned_messages:
                    e = self._get_emotion(clean_txt)
                    for k, v in e.items():
                        all_emotions[k].append(v)
                    all_messages_out.append({
                        "text": orig_msg["text"],
                        "time": orig_msg.get("time"),
                        "emotion_scores": e
                    })

                total_messages_count += len(cleaned_messages)

            if not all_emotions:
                return {
                    "messages_count": 0,
                    "emotions_median": {"negative": 0.0, "neutral": 0.0, "positive": 0.0},
                    "topics": [],
                    #"messages": []
                }

            # Объединяем медианы по всем батчам
            emotions_median = {k: round(statistics.median(vs), 3) for k, vs in all_emotions.items()}
            for k in ["negative", "neutral", "positive"]:
                emotions_median.setdefault(k, 0.0)

            sort = sorted(emotions_median, key=emotions_median.get, reverse=True)
            if sort[0] == "neutral":
                dominant_emotion = sort[1] if len(sort) > 1 else sort[0]
            else:
                dominant_emotion = sort[0]

            return {
                "messages_count": total_messages_count,
                "dominant_emotion": dominant_emotion,
                "emotions_median": emotions_median,
                "text_dominant": self.sender_disc_analyze[sender]["text_dominant"],
                "test_dominant": self.sender_disc_analyze[sender]["test_dominant"],
                "type_descriptions": self.type_descriptions,
                # "messages": all_messages_out
            }

        messages = data.get("messages", [])
        if not messages:
            return {"dialog_id": data.get("dialog_id") or data.get("id"), "error": "Пустой диалог"}

        # Группируем по отправителям
        grouped = {}
        for msg in messages:
            sender = msg.get("sender")
            if sender:
                grouped.setdefault(sender, []).append(msg)

        # Получаем отправителей
        keys = list(grouped.keys())

        # Очищаем текст каждого участника диалога
        for sender in keys:
            text = grouped[sender]
            # Склеиваем все сообщения участника в один текст
            full_text = " ".join(msg.get("text", "") for msg in text if msg.get("text"))
            cleaned = self._clean_text(full_text)
            self.sender_clean_text[sender] = cleaned

            disc_sender_analyzer = DISCAnalyze(cleaned)
            text_dominant, test_dominant = disc_sender_analyzer.analyze(1)

            self.sender_disc_analyze[sender] = {"text_dominant": text_dominant, "test_dominant": test_dominant}

        participants_data = {}
        for sender, msgs in grouped.items():
            try:
                participants_data[sender] = analyze_participant(sender, msgs)
            except Exception as e:
                participants_data[sender] = {"error": str(e)}

        return {
            "dialog_id": data.get("dialog_id") or data.get("id"),
            "title": data.get("title"),
            "participants_analysis": participants_data
        }, keys

    #---------------------------- MAIN ANALYZER ------------------------------
    def analyze(self, data):
        """Полный анализ диалога: темы, эмоции, DISC-профили участников."""
        # Анализ эмоций и DISC
        emotions_disc_result, senders = self._emotions_analyze(data)
        # Анализ тем
        topics_result = TopicAnalyzer().analyze(
            messages=data.get("messages", []),
            participants=senders
        )

        # Если в emotions_disc_result есть ошибка — возвращаем её
        if "error" in emotions_disc_result:
            return emotions_disc_result

        # Объединяем результаты
        combined_result = {
            "dialog_id": emotions_disc_result["dialog_id"],
            "title": emotions_disc_result.get("title"),
            "total_messages_analyzed": topics_result["total_messages_analyzed"],
            "dominant_topics": topics_result["dominant_topics"],
            #"topic_transitions": topics_result["topic_transitions"],
            "participants_analysis": {}
        }

        # Обогащаем анализ каждого участника тематической информацией
        for sender, emotion_disc_data in emotions_disc_result["participants_analysis"].items():
            participant_topics = topics_result["participant_interests"].get(sender, {})
            combined_result["participants_analysis"][sender] = {
                **emotion_disc_data,  # эмоции, DISC и сообщения
                "topic_interests": participant_topics  # добавляем темы
            }

        return combined_result

