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

class AnimalResponse(BaseModel):
    id: int
    type: str
    name: str

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

class AnimalDetail(AnimalResponse):
    abilities: dict