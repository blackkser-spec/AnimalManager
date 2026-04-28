from core import animal
from .exceptions import AnimalNotFoundError, ValidationError
import random

class AnimalManager:
    SEARCH_MAP = {
        "id": lambda a: [str(a.id)],
        "type": lambda a: [(a.type_en or "").lower(), (a.type_jp or "")],
        "name": lambda a: [a.name.lower()],
        "ability": lambda a: list(a.get_all_ability().keys())
    }
    ALLOWED_SORT_KEYS = ["id", "type_en", "type_jp", "name"]
    ALLOWED_ACTIONS = ["voice", "fly", "swim"]
    EDITABLE_ATTRIBUTES = ["type", "name", "ability"]
    
    def __init__(self, repository):
        self.repository = repository
        self.id_counter = 0
        self.naming_count = {key: 0 for key in animal.AVAILABLE_ANIMAL_TYPES}
        self.animals = {}
        self._refresh_initial_state()

    def _get_serializable_data(self):
        """現在のマネージャの状態を辞書形式で取得する"""
        animal_list = []
        for a in self.animals.values():
            animal_list.append(a.to_dict())
        return {"id_counter": self.id_counter, "naming_count": self.naming_count, "animals": animal_list}

    def _refresh_initial_state(self):
        self.initial_state_data = self._get_serializable_data()

    def is_changed(self):
        return self.initial_state_data != self._get_serializable_data()
    
    # --- get method ---
    
    def get_animal(self, animal_id, raise_error=True):
        animal = self.animals.get(animal_id)
        if raise_error and animal is None:
            raise AnimalNotFoundError(animal_id)
        return animal
    
    def get_all_animals(self):
        return sorted(self.animals.values(), key=lambda x: x.id)    

    def get_available_animal_types(self):
        return list(animal.AVAILABLE_ANIMAL_TYPES.keys())

    def get_available_abilities(self):
        return list(animal.AVAILABLE_ABILITIES.keys())

    def _validate_name(self, name):
        if not name or not name.strip():
            raise ValidationError("name_empty")
        if len(name) > 20:
            raise ValidationError("name_too_long")

    def add_animal(self, animal_type, name):
        target = animal.AVAILABLE_ANIMAL_TYPES.get(animal_type)
        if target is None: raise ValidationError("invalid_animal_type")
        
        self._validate_name(name)
        self.id_counter += 1
        animal_instance = target(self.id_counter, name)
        self.animals[self.id_counter] = animal_instance

        return animal_instance

    def add_random_animal(self, count):
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

    def remove_animal(self, animal_id):
        self.get_animal(animal_id)
        return self.animals.pop(animal_id)
    
    def edit_animal(self, animal_id, attr, new_value):
        edit_map = {
            "type": self._edit_animal_type,
            "name": self._edit_animal_name,
            "ability": self._edit_animal_ability,
        }
        if attr not in edit_map:
            raise ValidationError("invalid_selection")
        return edit_map[attr](animal_id, new_value)

    def _edit_animal_type(self, animal_id, new_type):
        target_animal = self.get_animal(animal_id)
        
        if new_type not in animal.AVAILABLE_ANIMAL_TYPES:
            raise ValidationError("invalid_animal_type")

        cls = animal.AVAILABLE_ANIMAL_TYPES[new_type]
        new_animal = cls(target_animal.id, target_animal.name)
        new_animal.ex_ability = target_animal.ex_ability
        self.animals[target_animal.id] = new_animal
        return new_animal
    
    def _edit_animal_name(self, animal_id, new_name):
        target_animal = self.get_animal(animal_id)
        self._validate_name(new_name)
        target_animal.name = new_name
        return target_animal

    def _edit_animal_ability(self, animal_id, new_ability):
        target_animal = self.get_animal(animal_id)
        if new_ability not in animal.AVAILABLE_ABILITIES:
            raise ValidationError("invalid_ability")
            
        target_animal.ex_ability[new_ability] = dict(animal.AVAILABLE_ABILITIES[new_ability])
        return target_animal

    def act_animal(self, action_name):
        """指定された行動を、可能な全ての動物に実行させる"""
        if not action_name:
            return []
        if action_name not in self.ALLOWED_ACTIONS:
            raise ValidationError("invalid_action")

        # アクション名が AVAILABLE_ABILITIES に存在すれば、それを必須特技とする
        # voice などの基本アクションは required_ability が None になる
        required_ability = action_name if action_name in animal.AVAILABLE_ABILITIES else None

        results = [] 
        for a in self.animals.values():
            # 必要な能力を持っているか、または能力が不要な行動（voiceなど）かを確認
            if required_ability is None or a.has_ability(required_ability):
                if hasattr(a, action_name):
                    method = getattr(a, action_name) 
                    result = method()
                    if result:
                        results.append(result)
        return results

    def sort_list(self, target_list, category):
        if category not in self.ALLOWED_SORT_KEYS:
            raise ValidationError("invalid_sort_key")
        return sorted(target_list, key=lambda a: getattr(a, category)) 

    def clear_data(self):
        self.animals.clear()
        self.id_counter = 0
        self.naming_count = {key: 0 for key in animal.AVAILABLE_ANIMAL_TYPES}
        self._refresh_initial_state()

    def search_animal(self, attr, keyword):
        """キーワードと属性で動物を検索する"""
        if attr != "all" and attr not in self.SEARCH_MAP:
            raise ValidationError("invalid_search_attr")

        if not keyword:
            return sorted(self.animals.values(), key=lambda x: x.id)

        keyword = keyword.lower()
        results = []
        for a in self.animals.values():
            if attr == "all":
                values = []
                for getter in self.SEARCH_MAP.values():
                    values.extend(getter(a))
            else:
                getter = self.SEARCH_MAP.get(attr)
                values = getter(a)
            if any(keyword in str(v).lower() for v in values):
                results.append(a)
                
        return sorted(results, key=lambda x: x.id)

    def save_to_file(self):
        data = self._get_serializable_data()
        self.repository.save(data)
        self._refresh_initial_state()

    def load_from_file(self):
        data = self.repository.load()
        if data is None:
            return

        self.animals.clear()
        self._restore_counters(data)
        self._restore_animals(data.get("animals", []))
        self._refresh_initial_state()

    def _restore_counters(self, data):
        self.id_counter = data.get("id_counter", 0)
        loaded_count = data.get("naming_count", {})
        for key in self.naming_count:
            if key in loaded_count:
                self.naming_count[key] = loaded_count[key]

    def _restore_animals(self, animal_data_list):
        for item in animal_data_list:
            animal_type = item.get("type_en")
            if not animal_type:
                continue

            cls = animal.AVAILABLE_ANIMAL_TYPES.get(animal_type)
            if cls:
                self.animals[item["id"]] = cls.from_dict(item)