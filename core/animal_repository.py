import json
import os
import datetime
from typing import Any
from pydantic import BaseModel, ValidationError as PydanticValidationError, Field
from core.exceptions import LoadError, SaveError


class AnimalSchema(BaseModel):
    id: int
    name: str
    animal_type: str
    ex_ability: list[str] = Field(default_factory=list)

class StorageSchema(BaseModel):
    id_counter: int
    naming_count: dict[str, int]
    animals: list[AnimalSchema]

class AnimalRepository:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def save(self, data: dict[str, Any]) -> None:
        try:
            validated_data = StorageSchema.model_validate(data)
            directory = os.path.dirname(self.file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
                
            with open(self.file_path, "w", encoding="UTF-8") as f:
                f.write(validated_data.model_dump_json(indent=4))
        except (PydanticValidationError, TypeError):
            raise SaveError("invalid_save_data")
        except OSError:
            raise SaveError("save_error")

    def load(self) -> dict[str, Any] | None:
        try:
            if not os.path.exists(self.file_path):
                return None

            try:
                with open(self.file_path, "r", encoding="UTF-8") as f:
                    raw_data = json.load(f)
                
                validated_data = StorageSchema.model_validate(raw_data)
                return validated_data.model_dump()

            except (json.JSONDecodeError, PydanticValidationError) as e:
                # 破損している場合はリネームして通知する（例外を投げる）
                base, ext = os.path.splitext(self.file_path)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                broken_path = f"{base}_broken_{timestamp}{ext}"
                os.rename(self.file_path, broken_path)
                
                reason_key = "json_syntax_error" if isinstance(e, json.JSONDecodeError) else "data_inconsistency"
                raise LoadError("file_broken_moved", path=broken_path, reason=reason_key)

        except OSError:
            raise LoadError("load_error")
