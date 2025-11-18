# convert_to_sqlite.py
import sqlite3
import json
import os

DB_PATH = "/home/fedosdan2/prog/pr_act/PROJECT/backend/analysis.db"
JSON_DIR = "/home/fedosdan2/prog/pr_act/PROJECT/backend/analysis_results"

def init_db(conn):
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")

    c.execute("""
        CREATE TABLE IF NOT EXISTS dialogs (
            dialog_id TEXT PRIMARY KEY,
            title TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            dialog_id TEXT,
            sender TEXT,
            messages_count INTEGER,
            emotion_negative REAL,
            emotion_neutral REAL,
            emotion_positive REAL,
            topic_ratios_json TEXT,
            PRIMARY KEY (dialog_id, sender),
            FOREIGN KEY (dialog_id) REFERENCES dialogs(dialog_id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dialog_id TEXT,
            sender TEXT,
            text TEXT,
            time TEXT,
            emotion_negative REAL,
            emotion_neutral REAL,
            emotion_positive REAL,
            topic_id INTEGER,
            FOREIGN KEY (dialog_id) REFERENCES dialogs(dialog_id) ON DELETE CASCADE
        )
    """)
    conn.commit()

def insert_json_to_db(conn, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "error" in data:
        print(f"⚠️ Пропуск {json_path}: ошибка на уровне диалога")
        return

    dialog_id = data.get("dialog_id") or data.get("id")
    if not dialog_id:
        print(f"⚠️ Нет dialog_id в {json_path}")
        return

    title = data.get("title", "")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO dialogs (dialog_id, title) VALUES (?, ?)", (dialog_id, title))

    for sender, analysis in data.get("participants_analysis", {}).items():
        if "error" in analysis:
            print(f"⚠️ Ошибка у участника {sender} в {dialog_id}: {analysis['error']}")
            continue

        emo = analysis.get("emotions_median", {})
        c.execute("""
            INSERT OR REPLACE INTO participants (
                dialog_id, sender, messages_count,
                emotion_negative, emotion_neutral, emotion_positive,
                topic_ratios_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            dialog_id,
            sender,
            analysis["messages_count"],
            emo.get("negative", 0.0),
            emo.get("neutral", 0.0),
            emo.get("positive", 0.0),
            json.dumps(analysis.get("topic_ratios", {}), ensure_ascii=False)
        ))

        for msg in analysis.get("messages", []):
            emo_msg = msg.get("emotion_scores", {})
            c.execute("""
                INSERT INTO messages (
                    dialog_id, sender, text, time,
                    emotion_negative, emotion_neutral, emotion_positive, topic_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dialog_id,
                sender,
                msg.get("text", ""),
                msg.get("time"),
                emo_msg.get("negative", 0.0),
                emo_msg.get("neutral", 0.0),
                emo_msg.get("positive", 0.0),
                msg.get("topic_id")  # ✅ теперь есть!
            ))

    conn.commit()
    print(f"✅ Импортировано: {os.path.basename(json_path)}")

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    for fname in os.listdir(JSON_DIR):
        if fname.endswith("_analysis.json"):
            insert_json_to_db(conn, os.path.join(JSON_DIR, fname))

    conn.close()
    print(f"✅ Все данные сохранены в {DB_PATH}")

if __name__ == "__main__":
    main()