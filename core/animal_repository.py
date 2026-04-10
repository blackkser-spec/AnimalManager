import json
import os
from pydantic import BaseModel, ValidationError, Field

class AnimalSchema(BaseModel):
    id: int
    name: str
    type_en: str
    type_jp: str
    ex_ability: dict = Field(default_factory=dict)

class StorageSchema(BaseModel):
    id_counter: int
    naming_count: dict[str, int]
    animals: list[AnimalSchema]

class AnimalRepository:
    def __init__(self, file_path):
        self.file_path = file_path

    def save(self, data):
        try:
            validated_data = StorageSchema.model_validate(data)

            directory = os.path.dirname(self.file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
                
            with open(self.file_path, "w", encoding="UTF-8") as f:
                f.write(validated_data.model_dump_json(indent=4))
            return True
        except (IOError, ValidationError):
            return False

    def load(self):
        try:
            if not os.path.exists(self.file_path):
                return None

            with open(self.file_path, "r", encoding="UTF-8") as f:
                raw_data = json.load(f)
            
            validated_data = StorageSchema.model_validate(raw_data)
            return validated_data.model_dump()

        except (FileNotFoundError, OSError):
            return None
        except (json.JSONDecodeError, ValidationError):
            try:
                base, ext = os.path.splitext(self.file_path)
                os.rename(self.file_path, f"{base}_broken{ext}")
            except:
                pass
            return None
