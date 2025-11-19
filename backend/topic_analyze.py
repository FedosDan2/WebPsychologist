# topic_analyze.py
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

# Загружаем ОДИН РАЗ (глобально)
_model = None
_tokenizer = None

def get_model():
    global _model, _tokenizer
    if _model is None:
        print("📥 Загружаем rut5-base-absum...")
        _model = T5ForConditionalGeneration.from_pretrained("cointegrated/rut5-base-absum")
        _tokenizer = T5Tokenizer.from_pretrained("cointegrated/rut5-base-absum")
        if torch.cuda.is_available():
            _model.cuda()
    return _model, _tokenizer

def extract_topics_from_dialog(messages, max_length=64):
    # Объединяем диалог в текст
    dialog = "\n".join([
        f"{m.get('sender', '')}: {m.get('text', '')}" 
        for m in messages 
        if m.get("text")
    ])
    
    if not dialog.strip():
        return ["пустой_диалог"]

    model, tokenizer = get_model()
    
    # T5 требует префикс задачи
    input_text = "заголовок: " + dialog
    input_ids = tokenizer(
        input_text,
        return_tensors="pt",
        max_length=512,
        truncation=True
    ).input_ids

    if torch.cuda.is_available():
        input_ids = input_ids.cuda()

    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            max_length=max_length,
            min_length=5,
            no_repeat_ngram_size=2,
            do_sample=False,  # детерминированно
            early_stopping=True
        )

    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Превращаем заголовок в темы: разбиваем по ключевым словам
    # Например: "Дети играют на кухне" → ["дети", "игра", "кухня"]
    keywords = summary.lower().strip(" .,").split()
    # Можно улучшить через простой фильтр (удалить стоп-слова), но и так сойдёт
    return keywords[:5]  # максимум 5 тем