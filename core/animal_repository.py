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
        except (ValidationError, TypeError):
            raise ValueError("保存データの形式が正しくありません")
        except OSError:
            raise IOError("ファイルの書き込み権限がないか、ディスクがいっぱいです")

    def load(self):
        try:
            if not os.path.exists(self.file_path):
                return None

            try:
                with open(self.file_path, "r", encoding="UTF-8") as f:
                    raw_data = json.load(f)
                
                validated_data = StorageSchema.model_validate(raw_data)
                return validated_data.model_dump()

            except (json.JSONDecodeError, ValidationError) as e:
                # 破損している場合はリネームして通知する（例外を投げる）
                base, ext = os.path.splitext(self.file_path)
                broken_path = f"{base}_broken{ext}"
                os.rename(self.file_path, broken_path)
                
                reason = "JSONの記述ミス" if isinstance(e, json.JSONDecodeError) else "データの不整合"
                raise ValueError(f"データファイル破損のため {broken_path} に退避しました ({reason})")

        except OSError:
            raise IOError("データファイルの読み込みに失敗しました（アクセス権限等）")
