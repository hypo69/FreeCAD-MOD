# project_manager.py
import os
import json
from pathlib import Path

AI_DATA_DIR = os.path.join(os.path.expanduser("~"), ".FreeCAD", "AIAssistant", "data")
PROJECT_FILE = os.path.join(AI_DATA_DIR, "project.json")

# Создаём папку при импорте
os.makedirs(AI_DATA_DIR, exist_ok=True)

class AIProject:
    def __init__(self):
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(PROJECT_FILE):
            try:
                with open(PROJECT_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"links": {}}  # links: {"image.png": "prompt_1.md"}
    
    def save(self):
        with open(PROJECT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def link_text_to_image(self, image_file, text_file):
        self.data["links"][image_file] = text_file
        self.save()
    
    def unlink_image(self, image_file):
        if image_file in self.data["links"]:
            del self.data["links"][image_file]
            self.save()
    
    def get_linked_text(self, image_file):
        return self.data["links"].get(image_file)
    
    def get_all_links(self):
        return self.data["links"].copy()
    
    def is_image_linked(self, image_file):
        return image_file in self.data["links"]