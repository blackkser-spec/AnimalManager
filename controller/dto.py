from dataclasses import dataclass

@dataclass(frozen=True)
class AnimalDTO:
    id: int
    name: str
    animal_type: str
    abilities: list[str]
