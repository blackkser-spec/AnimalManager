from pydantic import BaseModel
from enum import Enum

class AnimalTypes(str, Enum):
    bird    = "bird"
    cat     = "cat"
    dog     = "dog"
    duck    = "duck"
    fish    = "fish"
    penguin = "penguin"

class Animal(BaseModel):
    type: str
    name: str

class AnimalResult(BaseModel):
    id  : int
    name: str

class AnimalDetail(BaseModel):
    id       : int
    type_en  : str
    type_jp  : str
    name     : str
    abilities: dict = {}

class AnimalEdit(BaseModel):
    type: AnimalTypes | None = None
    name: str | None = None
    ability: str | None = None

class SearchAttr(str, Enum):
    all = "すべて"
    id = "ID"
    type = "種類"
    name = "名前"
    ability = "特技"

class SortAttr(str, Enum):
    id      = "ID"
    type_en = "種類:英語"
    type_jp = "種類:日本語"
    name    = "名前"

class AbilityType(str, Enum):
    voice = "voice"
    fly   = "fly"
    swim  = "swim"
