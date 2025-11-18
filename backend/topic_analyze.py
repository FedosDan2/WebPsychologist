from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Загрузка модели в 4-битном режиме (экономия памяти)
model_id = "microsoft/Phi-3-mini-4k-instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.float16,       # или "auto"
    trust_remote_code=True,
    load_in_4bit=True                # ← квантование до 4 бит
)

def extract_topics_from_dialog(messages, max_new_tokens=100):
    # Объединяем сообщения в один текст
    dialog_text = "\n".join([f"{m.get('sender', '')}: {m.get('text', '')}" for m in messages])
    
    prompt = f"""Определи основные темы этого диалога. Ответь списком тем через запятую, c пояснениями.

        Диалог:
        {dialog_text}

        Темы:"""

    messages_prompt = [
        {"role": "user", "content": prompt}
    ]

    input_ids = tokenizer.apply_chat_template(
        messages_prompt,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=False,         # детерминированно
        pad_token_id=tokenizer.eos_token_id
    )

    response = outputs[0][input_ids.shape[-1]:]
    topics_str = tokenizer.decode(response, skip_special_tokens=True).strip()
    
    # Разбиваем на список
    topics = [t.strip() for t in topics_str.split(",") if t.strip()]
    return topics