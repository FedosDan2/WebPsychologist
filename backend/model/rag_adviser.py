import json
import os
import hashlib
from typing import List, Dict, Any
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
from llama_cpp import Llama
import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


class RAGPsychologyAdvisor:
    def __init__(self, knowledge_base_path: str = "psychology_knowledge_base.json"):
        # === 1. Загружаем LLM ===
        print("📥 Загружаем LLM (Saiga Mistral 7B GGUF)...")
        self.llm = Llama(
            model_path="/home/fedosdan2/prog/pr_act/PROJECT/backend/model/mistral/saiga_mistral_7b.Q4_K_M.gguf",
            n_ctx=2048,
            n_threads=6,  # количество CPU-потоков
            verbose=False
        )

        # === 2. Загружаем базу знаний ===
        print(f"📚 Загружаем базу знаний: {knowledge_base_path}")
        with open(knowledge_base_path, "r", encoding="utf-8") as f:
            self.knowledge_base = json.load(f)

        # === 3. Загружаем эмбеддинг-модель (на CPU) ===
        print("🧠 Загружаем эмбеддинг-модель...")
        self.embedding_model = SentenceTransformer('intfloat/multilingual-e5-large', device='cpu')

        # === 4. Загружаем или создаём FAISS-индекс с кэшированием ===
        self._load_or_build_index(knowledge_base_path)

        print("✅ RAG-система готова к работе!")

    def _compute_file_hash(self, filepath: str) -> str:
        """Вычисляет хеш файла для отслеживания изменений."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _load_or_build_index(self, knowledge_base_path: str):
        """Загружает индекс из кэша или создаёт новый."""
        # Определяем пути к кэш-файлам
        cache_dir = "rag_cache"
        os.makedirs(cache_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(knowledge_base_path))[0]
        index_path = os.path.join(cache_dir, f"{base_name}.faiss")
        texts_path = os.path.join(cache_dir, f"{base_name}_texts.json")
        hash_path = os.path.join(cache_dir, f"{base_name}.hash")

        # Вычисляем текущий хеш базы знаний
        current_hash = self._compute_file_hash(knowledge_base_path)

        # Проверяем, есть ли актуальный кэш
        if (os.path.exists(index_path) and
            os.path.exists(texts_path) and
            os.path.exists(hash_path)):

            with open(hash_path, "r") as f:
                cached_hash = f.read().strip()
            if cached_hash == current_hash:
                print("🔍 Загружаем кэшированный FAISS-индекс...")
                self.index = faiss.read_index(index_path)
                with open(texts_path, "r", encoding="utf-8") as f:
                    self.kb_texts = json.load(f)
                return

        # Если кэш отсутствует или устарел — создаём новый
        print("🔍 Кэш отсутствует или устарел. Создаём новый индекс...")
        self._build_faiss_index()

        # Сохраняем индекс, тексты и хеш
        faiss.write_index(self.index, index_path)
        with open(texts_path, "w", encoding="utf-8") as f:
            json.dump(self.kb_texts, f, ensure_ascii=False)
        with open(hash_path, "w") as f:
            f.write(current_hash)

    def _build_faiss_index(self):
        """Создаёт FAISS-индекс на основе базы знаний."""
        self.kb_texts = []
        for item in self.knowledge_base:
            text = " ".join(item.get("keywords", [])) + " " + item["content"]
            self.kb_texts.append(text)

        print("  → Генерация эмбеддингов...")
        embeddings = self.embedding_model.encode(
            self.kb_texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype('float32')

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)
        print(f"  → Индекс создан. Векторов: {self.index.ntotal}")

    def _retrieve_relevant_facts(self, query: str, top_k: int = 3) -> List[Dict]:
        """Извлекает top_k релевантных цитат из базы знаний."""
        query_emb = self.embedding_model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype('float32')
        query_emb = np.expand_dims(query_emb, axis=0)

        distances, indices = self.index.search(query_emb, top_k)

        results = []
        for idx in indices[0]:
            if idx < len(self.knowledge_base):
                results.append(self.knowledge_base[idx])
        return results

    def _build_prompt(self, analysis: Dict[str, Any], retrieved_facts: List[Dict]) -> str:
        """Формирует промпт для LLM."""
        summary_lines = []
        summary_lines.append(f"Диалог: {analysis.get('title', 'Неизвестно')}")
        summary_lines.append(f"Проанализировано сообщений: {analysis.get('total_messages_analyzed', 0)}")

        dominant = [f"{t['topic']} ({t['percentage']}%)" for t in analysis.get('dominant_topics', [])]
        if dominant:
            summary_lines.append(f"Основные темы: {', '.join(dominant)}")

        participants_info = []
        for name, data in analysis.get('participants_analysis', {}).items():
            emotion = data.get('dominant_emotion', 'не определена')
            disc_raw = data.get('text_dominant', 'не определён')
            if isinstance(disc_raw, list):
                disc_str = "/".join([str(x) for x in disc_raw if isinstance(x, str)])
            elif isinstance(disc_raw, str):
                disc_str = disc_raw
            else:
                disc_str = "не определён"
            main_topic = data.get('topic_interests', {}).get('main_interest', 'не определена')
            participants_info.append(f"- {name}: доминирующая эмоция — {emotion}, стиль DISC — {disc_str}, интересы — {main_topic}")
        
        if participants_info:
            summary_lines.append("Участники:\n" + "\n".join(participants_info))

        analysis_summary = "\n".join(summary_lines)

        facts_text = "\n".join([
            f"• {item['content']} (Источник: {item['source']})"
            for item in retrieved_facts
        ]) or "Нет релевантных данных."

        prompt = f"""Ты — лицензированный психолог с 15-летним стажем. На основе анализа переписки и научных данных дай краткий, практичный и обоснованный совет.

Анализ переписки:
{analysis_summary}

Релевантные научные данные:
{facts_text}

Требования:
- Давай 3-5 конкретных совета.
- Ссылаёшься на источники: «Как отмечает Дж. Готтман…», «Согласно модели DISC…».
- Избегай общих фраз вроде «нужно лучше общаться».
- Пиши на русском, в поддерживающем, но профессиональном тоне.
- Ответ должен быть не длиннее 500 слов.

Ответ:"""
        return prompt

    def generate_advice(self, analysis: Dict[str, Any]) -> str:
        """Генерирует совет на основе анализа и RAG."""
        topics = [t["topic"] for t in analysis.get("dominant_topics", [])]
        emotions = list({data.get("dominant_emotion") for data in analysis.get("participants_analysis", {}).values() if data.get("dominant_emotion")})
        
        disc_tokens = set()
        for data in analysis.get("participants_analysis", {}).values():
            for key in ["text_dominant", "test_dominant"]:
                val = data.get(key)
                if isinstance(val, list):
                    for v in val:
                        if isinstance(v, str):
                            disc_tokens.add(v)
                elif isinstance(val, str):
                    disc_tokens.add(val)
        disc_list = sorted(disc_tokens)

        query = f"{' '.join(topics)} {' '.join(emotions)} {' '.join(disc_list)}"
        query = query.strip() or "общий психологический анализ межличностной коммуникации"

        retrieved = self._retrieve_relevant_facts(query, top_k=3)
        prompt = self._build_prompt(analysis, retrieved)

        try:
            output = self.llm(
                prompt,
                max_tokens=256,       # ← не больше 128!
                temperature=0.7,
                stop=["Анализ переписки:", "Релевантные научные данные:", "\n\n"],
                echo=False
            )
            return output["choices"][0]["text"].strip()
        except Exception as e:
            return f"Ошибка генерации: {e}"