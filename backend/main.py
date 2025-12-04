import json, os
from analyzers.emotion_class import MainAnalyzer
from model.psych_advisor import PsychAdvisor
from model.rag_adviser import RAGPsychologyAdvisor

def main():
    out_dir = "/home/fedosdan2/prog/pr_act/PROJECT/analysis_results"
    os.makedirs(out_dir, exist_ok=True)
    
    # Читаем диалог из jsom
    fpath = "/home/fedosdan2/prog/pr_act/PROJECT/dialogs/1.json"
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"error": f"Ошибка чтения файла {fpath}: {e}"}
    
    analyzer = MainAnalyzer()
    res = analyzer.analyze(data)
    #model = PsychAdvisor()
    #advice = model.get_recommendations(res)
    rag_advisor = RAGPsychologyAdvisor(knowledge_base_path="/home/fedosdan2/prog/pr_act/PROJECT/lib_liter/literature_data.json")
    advice = rag_advisor.generate_advice(res)
    print(advice)
    
    f = os.path.basename(fpath)
    out_path = os.path.join(out_dir, f"{os.path.splitext(f)[0]}_analysis.json")
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump(advice, out, indent=2, ensure_ascii=False)

    
    print(f"✅ {f} → сохранён в {out_path}")

if __name__ == "__main__":
    main()