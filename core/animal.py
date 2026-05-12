from typing import Any

class Animal:
    def __init__(self, id: int, name: str, animal_type: str, ability: set[str] | None = None, ex_ability: set[str] | None = None) -> None:
        self.id          = id
        self.name        = name
        self.animal_type = animal_type
        self.ability     = ability or set()
        self.ex_ability  = ex_ability or set()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "animal_type": self.animal_type,
            "ex_ability": list(self.ex_ability)
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Animal':
        if cls is Animal:
            instance = cls(data["id"], data["name"], animal_type=data["animal_type"])
        else:
            instance = cls(data["id"], data["name"])
        instance.ex_ability = set(data.get("ex_ability", []))
        return instance

    def get_all_ability(self) -> set[str]:
        return self.ability | self.ex_ability

    def has_ability(self, ability_name: str) -> bool:
        return ability_name in self.get_all_ability()
    
    def sound(self) -> str | None:
        return "sound" if self.has_ability("sound") else None

    def fly(self) -> str | None:
        return "fly" if self.has_ability("fly") else None

    def swim(self) -> str | None:
        return "swim" if self.has_ability("swim") else None

class Bird(Animal):
    def __init__(self, id: int, name: str) -> None:
        super().__init__(id, name, animal_type="bird",
                         ability  ={"sound", "fly"})

class Cat(Animal):
    def __init__(self, id: int, name: str) -> None:
        super().__init__(id, name, animal_type="cat",
                         ability  ={"sound"})

class Dog(Animal):
    def __init__(self, id: int, name: str) -> None:
        super().__init__(id, name, animal_type="dog",
                         ability  ={"sound"})

class Duck(Animal):
    def __init__(self, id: int, name: str) -> None:
        super().__init__(id, name, animal_type="duck",
                         ability  ={"sound", "fly", "swim"})

class Fish(Animal):
    def __init__(self, id: int, name: str) -> None:
        super().__init__(id, name, animal_type="fish",
                         ability  ={"swim"})

class Penguin(Animal):
    def __init__(self, id: int, name: str) -> None:
        super().__init__(id, name, animal_type="penguin",
                         ability  ={"sound", "swim"})

class Sheep(Animal):
    def __init__(self, id: int, name: str) -> None:
        super().__init__(id, name, animal_type="sheep",
                         ability  ={"sound"})

AVAILABLE_ANIMAL_TYPES: dict[str, type[Animal]] = {
    "bird": Bird,
    "cat": Cat,
    "dog": Dog,
    "duck": Duck,
    "fish": Fish,
    "penguin": Penguin,
    "sheep": Sheep,
}

AVAILABLE_ABILITIES: set[str] = {
    "sound",
    "fly",
    "swim",
}