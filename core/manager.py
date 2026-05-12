from core import animal
from .exceptions import AnimalNotFoundError, ValidationError
import random
from typing import Any

class AnimalManager:
    SEARCH_MAP = {
        "all": lambda a: [str(a.id), a.animal_type.lower(), a.name.lower()] + list(a.get_all_ability()),
        "id": lambda a: [str(a.id)],
        "animal_type": lambda a: [a.animal_type.lower()],
        "name": lambda a: [a.name.lower()],
        "ability": lambda a: list(a.get_all_ability())
    }
    ALLOWED_SORT_KEYS: list[str] = ["id", "animal_type", "name"]
    ALLOWED_ACTIONS: list[str] = ["sound", "fly", "swim"]
    EDITABLE_ATTRIBUTES: list[str] = ["animal_type", "name", "ability"]
    
    def __init__(self, repository) -> None:
        self.repository = repository
        self.id_counter: int = 0
        self.naming_count: dict[str, int] = {key: 0 for key in animal.AVAILABLE_ANIMAL_TYPES}
        self.animals: dict[int, animal.Animal] = {}
        self._refresh_initial_state()

    def _get_serializable_data(self) -> dict[str, object]:
        """現在のマネージャの状態を辞書形式で取得する"""
        animal_list = []
        for a in self.animals.values():
            animal_list.append(a.to_dict())
        return {"id_counter": self.id_counter, "naming_count": self.naming_count, "animals": animal_list}

    def _refresh_initial_state(self) -> None:
        self.initial_state_data = self._get_serializable_data()

    def is_changed(self) -> bool:
        return self.initial_state_data != self._get_serializable_data()
    
    # --- get method ---
    
    def get_animal(self, animal_id: int, raise_error: bool = True) -> animal.Animal | None:
        target_animal = self.animals.get(animal_id)
        if raise_error and target_animal is None:
            raise AnimalNotFoundError(animal_id)
        return target_animal
    
    def get_all_animals(self) -> list[animal.Animal]:
        return sorted(self.animals.values(), key=lambda x: x.id)    

    def get_available_animal_types(self) -> list[str]:
        return list(animal.AVAILABLE_ANIMAL_TYPES.keys())

    def get_available_abilities(self) -> list[str]:
        return list(animal.AVAILABLE_ABILITIES)

    def _validate_name(self, name: str) -> None:
        if not name or not name.strip():
            raise ValidationError("name_empty")
        if len(name) > 20:
            raise ValidationError("name_too_long")

    def add_animal(self, animal_type: str, name: str) -> animal.Animal:
        target = animal.AVAILABLE_ANIMAL_TYPES.get(animal_type)
        if target is None: raise ValidationError("invalid_animal_type", animal_type=animal_type)
        
        self._validate_name(name)
        self.id_counter += 1
        animal_instance = target(self.id_counter, name)
        self.animals[self.id_counter] = animal_instance

        return animal_instance

    def add_random_animal(self, count: int) -> list[animal.Animal]:
        if not isinstance(count, int):
            raise ValidationError("require_int")
        if count <= 0:
            raise ValidationError("require_positive_int")
        
        added_animals = []
        for _ in range(count):
            animal_type = random.choice(list(animal.AVAILABLE_ANIMAL_TYPES.keys()))
            self.naming_count[animal_type] += 1
            name   = f"{animal_type}{self.naming_count[animal_type]}"
            added_animals.append(self.add_animal(animal_type, name))
        return added_animals

    def remove_animal(self, animal_id: int) -> animal.Animal:
        if not isinstance(animal_id, int):
            raise ValidationError("require_int")
        self.get_animal(animal_id)
        return self.animals.pop(animal_id)
    
    def edit_animal(self, animal_id: int, attr: str, new_value: str) -> animal.Animal:
        edit_map = {
            "animal_type": self._edit_animal_type,
            "name": self._edit_animal_name,
            "ability": self._edit_animal_ability,
        }
        if attr not in edit_map:
            raise ValidationError("invalid_attribute")
        return edit_map[attr](animal_id, new_value)

    def _edit_animal_type(self, animal_id: int, new_type: str) -> animal.Animal:
        target_animal = self.get_animal(animal_id)
        
        if new_type not in animal.AVAILABLE_ANIMAL_TYPES:
            raise ValidationError("invalid_animal_type")

        cls = animal.AVAILABLE_ANIMAL_TYPES[new_type]
        new_animal = cls(target_animal.id, target_animal.name)
        new_animal.ex_ability = target_animal.ex_ability
        self.animals[target_animal.id] = new_animal
        return new_animal
    
    def _edit_animal_name(self, animal_id: int, new_name: str) -> animal.Animal:
        target_animal = self.get_animal(animal_id)
        self._validate_name(new_name)
        target_animal.name = new_name
        return target_animal

    def _edit_animal_ability(self, animal_id: int, new_ability: str) -> animal.Animal:
        target_animal = self.get_animal(animal_id)
        if new_ability not in animal.AVAILABLE_ABILITIES:
            raise ValidationError("invalid_ability")
            
        target_animal.ex_ability.add(new_ability)
        return target_animal

    def act_animal(self, action_name: str) -> list[dict[str, Any]]:
        """指定された行動を、可能な全ての動物に実行させる"""
        if not action_name:
            return []
        if action_name not in self.ALLOWED_ACTIONS:
            raise ValidationError("invalid_action")
        # 共通ability用 require
        required_ability = action_name if action_name in animal.AVAILABLE_ABILITIES else None

        results = [] 
        for a in self.animals.values():
            # 必要な能力を持っているか
            if required_ability is None or a.has_ability(required_ability):
                if hasattr(a, action_name):
                    method = getattr(a, action_name) 
                    result = method()
                    if result:
                        results.append({
                            "animal": a,
                            "action_key": result
                        })
        return results

    def sort_list(self, target_list: list[animal.Animal], sort_key: str) -> list[animal.Animal]:
        if sort_key not in self.ALLOWED_SORT_KEYS:
            raise ValidationError("invalid_sort_key")
        return sorted(target_list, key=lambda a: getattr(a, sort_key)) 

    def clear_data(self) -> None:
        self.animals.clear()
        self.id_counter = 0
        self.naming_count = {key: 0 for key in animal.AVAILABLE_ANIMAL_TYPES}
        self._refresh_initial_state()

    def search_animal(self, attr: str, keyword: str) -> list[animal.Animal]:
        """キーワードと属性で動物を検索する"""
        if attr not in self.SEARCH_MAP:
            raise ValidationError("invalid_search_attr")

        if not keyword:
            return self.get_all_animals()

        keyword = keyword.lower()
        results = []
        getter = self.SEARCH_MAP[attr]
        for a in self.animals.values():
            values = getter(a)
            if any(keyword in str(v).lower() for v in values):
                results.append(a)
                
        return sorted(results, key=lambda x: x.id)

    def save_to_file(self) -> None:
        data = self._get_serializable_data()
        self.repository.save(data)
        self._refresh_initial_state()

    def load_from_file(self) -> None:
        data = self.repository.load()
        if data is None:
            return

        self.animals.clear()
        self._restore_counters(data)
        self._restore_animals(data.get("animals", []))
        self._refresh_initial_state()

    def _restore_counters(self, data: dict[str, Any]) -> None:
        self.id_counter = data.get("id_counter", 0)
        self.naming_count = {key: 0 for key in animal.AVAILABLE_ANIMAL_TYPES}
        self.naming_count.update(data.get("naming_count", {}))

    def _restore_animals(self, animal_data_list: list[dict[str, Any]]) -> None:
        for item in animal_data_list:
            animal_type = item.get("animal_type")
            if not animal_type:
                continue

            cls = animal.AVAILABLE_ANIMAL_TYPES.get(animal_type)
            if cls:
                self.animals[item["id"]] = cls.from_dict(item)