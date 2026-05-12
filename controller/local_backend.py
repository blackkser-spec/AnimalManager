from typing import Any, Protocol
from .dto import AnimalDTO

class AnimalLike(Protocol):
    """Animalインスタンスが備えるべき最小限のインターフェース定義"""
    id: int
    name: str
    animal_type: str
    
    def get_all_ability(self) -> set[str]:
        ...

class LocalBackend:
    def __init__(self, layout: Any, manager: Any) -> None:
        self.layout = layout
        self.manager = manager
        self.manager.load_from_file()

    def execute_add(self, animal_type: str, name: str) -> None:
        self.manager.add_animal(animal_type, name)

    def execute_add_random(self, count: int) -> None:
        self.manager.add_random_animal(count)

    def execute_remove(self, animal_id: int) -> dict[str, str]:
        removed_animal = self.manager.remove_animal(animal_id)
        return {"id": removed_animal.id, "name": removed_animal.name}

    def execute_edit(self, animal_id: int, attr: str, new_value: str) -> None:
        self.manager.edit_animal(animal_id, attr, new_value)

    def execute_act(self, choice: str) -> list[dict[str, Any]]:
        raw_results = self.manager.act_animal(choice)
        return [
        {
            "name": item["animal"].name,
            "animal_type": item["animal"].animal_type,
            "action_key": item["action_key"]
        } for item in raw_results
    ]
    
    def is_valid_action(self, choice: str) -> bool:
        return choice in self.manager.ALLOWED_ACTIONS
    
    def execute_search(self, attribute: str, keyword: str) -> list[AnimalDTO]:
        animals = self.manager.search_animal(attribute, keyword)
        return [self._to_dto(a) for a in animals]

    def _to_dto(self, animal: AnimalLike) -> AnimalDTO:
        """AnimalLikeなオブジェクトをAnimalDTOに変換"""
        return AnimalDTO(
            id       = animal.id,
            name     = animal.name,
            animal_type  = animal.animal_type,
            abilities= list(animal.get_all_ability())
        )

    def execute_load(self) -> list[AnimalDTO]:
        return [self._to_dto(a) for a in self.manager.get_all_animals()]

    def save(self) -> bool:
        self.manager.save_to_file()
        return True

    def clear_data(self) -> None:
        self.manager.clear_data()
        self.manager.save_to_file()

    def has_unsaved_changes(self) -> bool:
        return self.manager.is_changed()
