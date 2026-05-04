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
    animal_type: str
    name: str

class AnimalResult(BaseModel):
    id  : int
    animal_type: AnimalTypes | None = None
    name: str

class AnimalDetail(BaseModel):
    id       : int
    animal_type  : str
    name     : str
    abilities: list = []

class AnimalEdit(BaseModel):
    animal_type: AnimalTypes | None = None
    name: str | None = None
    ability: str | None = None

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

class AbilityType(str, Enum):
    sound = "sound"
    fly   = "fly"
    swim  = "swim"

class ActionResult(BaseModel):
    name: str
    animal_type: str
    action_key: str
