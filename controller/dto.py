from dataclasses import dataclass

@dataclass(frozen=True)
class AnimalDTO:
    id: int
    name: str
    type_en: str
    type_jp: str
    abilities: list[str]
