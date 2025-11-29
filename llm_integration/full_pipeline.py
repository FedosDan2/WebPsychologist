import sys
import os

# Добавляем пути для импорта
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from psychological_models.disc_analyzer import DISCAnalyzer
from llm_integration.psych_advisor import PsychAdvisor

def run_full_analysis():
    """Полный пайплайн: анализ + рекомендации"""
    
    print("ЗАПУСК ПОЛНОГО АНАЛИЗА")
    print("=" * 50)
    
    # 1. Анализируем диск
    print("Анализирую стили общения...")
    disc_analyzer = DISCAnalyzer()
    
    files = [
        "backend/analysis_results/1_analysis.json", 
        "backend/analysis_results/2_analysis.json"
    ]
    
    all_results = {}
    
    for file_path in files:
        if os.path.exists(file_path):
            print(f"\nАнализ файла: {file_path}")
            analysis_result = disc_analyzer.analyze_dialog_file(file_path)
            
            disc_results = analysis_result['disc_results']
            dialog_title = analysis_result['dialog_title']
            
            all_results[file_path] = {
                'disc_results': disc_results,
                'dialog_title': dialog_title
            }
            
            # Выводим сырые результаты
            print(f"Диалог: {dialog_title}")
            for participant, data in disc_results.items():
                print(f"   👤 {participant}: {data['dominant_style']}-тип")
    
    # 2. Получаем рекомендации от LLM
    print("\nПодключаю психологическую модель...")
    advisor = PsychAdvisor()
    
    # Просим рекомендации для первого диалога
    first_file = files[0]
    if first_file in all_results:
        disc_results = all_results[first_file]['disc_results']
        dialog_title = all_results[first_file]['dialog_title']
        
        print(f"\nЗапрашиваю рекомендации для: {dialog_title}")
        
        advice = advisor.get_recommendations(disc_results, dialog_title)
        print("\nРЕКОМЕНДАЦИИ ОТ PSYCH-LLM:")
        print("=" * 50)
        print(advice)
        print("=" * 50)

if __name__ == "__main__":
    run_full_analysis()