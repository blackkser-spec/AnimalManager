import json
import os

class AnimalRepository:
    def __init__(self, file_path):
        self.file_path = file_path

    def save(self, data):
        try:
            directory = os.path.dirname(self.file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
                
            with open(self.file_path, "w", encoding="UTF-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except IOError:
            return False

    def load(self):
        try:
            with open(self.file_path, "r", encoding="UTF-8") as f:
                return json.load(f)
        except (FileNotFoundError, OSError):
            return None
        except json.JSONDecodeError:
            try:
                base, ext = os.path.splitext(self.file_path)
                os.rename(self.file_path, f"{base}_broken{ext}")
            except:
                pass
            return None
