from transformers import AutoTokenizer, AutoModelForCausalLM
import torch, json


# Глобальные переменные для кэширования модели
_model = None
_tokenizer = None

def get_phi3_model():
    """Загружает Phi-3-mini один раз и кэширует."""
    global _model, _tokenizer
    if _model is None:
        print("📥 Загружаем Phi-3-mini для интерпретации...")
        model_id = "microsoft/Phi-3-mini-4k-instruct"

        _tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True
        )
        _model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
            load_in_4bit=True  # экономия памяти
        )
        _model.eval()
    return _model, _tokenizer

def interpret_analysis(analysis_data, max_new_tokens=256):
    """
    Принимает словарь с метриками анализа и возвращает интерпретацию.
    
    Аргументы:
        analysis_data (dict): результат из analyze_dialog_by_participant
        max_new_tokens (int): макс. длина ответа
    
    Возвращает:
        str: человекочитаемый вывод
    """
    model, tokenizer = get_phi3_model()

    # Формируем промпт на русском с чёткими инструкциями
    prompt = f"""Ты — этичный и внимательный аналитик личных переписок. 
Твоя задача — на основе объективных метрик дать доброжелательный и фактологический вывод.
Не выдумывай, не ставь диагнозы, не оценивай личность. Говори только о поведении в этом диалоге.
Избегай общих фраз вроде «общались на разные темы». Делай акцент на эмоциях и темах.

Метрики анализа:
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

Вывод (на русском языке):"""

    messages = [{"role": "user", "content": prompt}]

    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # детерминированный результат
            pad_token_id=tokenizer.eos_token_id
        )

    response = outputs[0][input_ids.shape[-1]:]
    result = tokenizer.decode(response, skip_special_tokens=True).strip()
    return result