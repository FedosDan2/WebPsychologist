import json
import os
import glob

class DataLoader:
    def __init__(self):
        self.base_path = "backend"
        self.raw_dialogs_path = os.path.join(self.base_path, "dialogs")
        self.processed_dialogs_path = os.path.join(self.base_path, "analysis_results")
    
    def get_all_dialogs(self):
        """Возвращает все доступные диалоги с их путями и типами"""
        dialogs = []
        
        # 1. Ищем сырые диалоги (из папки dialogs)
        if os.path.exists(self.raw_dialogs_path):
            raw_files = glob.glob(os.path.join(self.raw_dialogs_path, "*.json"))
            for file_path in raw_files:
                dialogs.append({
                    'path': file_path,
                    'type': 'raw',
                    'name': os.path.basename(file_path)
                })
        
        # 2. Ищем обработанные диалоги (из папки analysis_results)  
        if os.path.exists(self.processed_dialogs_path):
            processed_files = glob.glob(os.path.join(self.processed_dialogs_path, "*.json"))
            for file_path in processed_files:
                dialogs.append({
                    'path': file_path,
                    'type': 'processed',
                    'name': os.path.basename(file_path)
                })
        
        return dialogs
    
    def load_dialog(self, file_path):
        """Загружает диалог по пути"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"❌ Ошибка загрузки файла {file_path}: {e}")
            return None
    
    def get_dialog_info(self, file_path):
        """Возвращает информацию о диалоге"""
        data = self.load_dialog(file_path)
        if not data:
            return None
        
        info = {
            'title': data.get('title', 'Без названия'),
            'participants': [],
            'messages_count': 0
        }
        
        # Для сырых данных
        if 'participants' in data:
            info['participants'] = data['participants']
            info['messages_count'] = len(data.get('messages', []))
        # Для обработанных данных
        elif 'participants_analysis' in data:
            info['participants'] = list(data['participants_analysis'].keys())
            total_messages = 0
            for participant_info in data['participants_analysis'].values():
                total_messages += participant_info.get('messages_count', 0)
            info['messages_count'] = total_messages
        
        return info

    def print_available_dialogs(self):
        """Печатает список всех доступных диалогов"""
        dialogs = self.get_all_dialogs()
        
        if not dialogs:
            print("❌ Диалоги не найдены! Проверь пути:")
            print(f"   Сырые диалоги: {self.raw_dialogs_path}")
            print(f"   Обработанные: {self.processed_dialogs_path}")
            return
        
        print("📁 ДОСТУПНЫЕ ДИАЛОГИ:")
        print("=" * 50)
        
        for i, dialog in enumerate(dialogs, 1):
            info = self.get_dialog_info(dialog['path'])
            if info:
                print(f"{i}. {dialog['name']} ({dialog['type']})")
                print(f"   📝 {info['title']}")
                print(f"   👥 Участники: {', '.join(info['participants'])}")
                print(f"   💬 Сообщений: {info['messages_count']}")
                print()

# Тестирование
if __name__ == "__main__":
    loader = DataLoader()
    loader.print_available_dialogs()
    
    # Дополнительная проверка
    print("🔍 ПРОВЕРКА ПУТЕЙ:")
    print(f"Существует ли backend/: {os.path.exists('backend')}")
    print(f"Существует ли backend/dialogs/: {os.path.exists('backend/dialogs')}")
    print(f"Существует ли backend/analysis_results/: {os.path.exists('backend/analysis_results')}")