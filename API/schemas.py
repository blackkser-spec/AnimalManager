from pydantic import BaseModel, field_validator
from enum import Enum
from core.animal import AVAILABLE_ANIMAL_TYPES, AVAILABLE_ABILITIES
from pydantic import Field

AnimalTypesEnum = Enum("AnimalTypes", {k: k for k in AVAILABLE_ANIMAL_TYPES}, type=str)
AbilityTypeEnum = Enum("AbilityType", {k: k for k in AVAILABLE_ABILITIES}, type=str)

class Animal(BaseModel):
    animal_type: str
    name: str

class AnimalResult(BaseModel):
    id  : int
    animal_type: str | None = None
    name: str

class AnimalDetail(BaseModel):
    id       : int
    animal_type  : str
    name     : str
    abilities: list[str] = Field(default_factory=list)

class AnimalEdit(BaseModel):
    animal_type: str | None = None
    name: str | None = None
    ability: str | None = None

    @field_validator("animal_type")
    @classmethod
    def validate_type(cls, v):
        if v is not None and v not in AVAILABLE_ANIMAL_TYPES:
            raise ValueError(f"Invalid animal type. Available: {list(AVAILABLE_ANIMAL_TYPES.keys())}")
        return v

class SearchAttr(str, Enum):
    all = "all"
    id = "id"
    animal_type = "animal_type"
    name = "name"
    ability = "ability"

class SortAttr(str, Enum):
    id      = "id"
    animal_type = "animal_type"
    name    = "name"

class ActionResult(BaseModel):
    name: str
    animal_type: str
    action_key: str
