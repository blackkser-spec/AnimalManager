from core import animal
import random
import json
import os

class AnimalNotFoundError(Exception):
    pass

class AnimalManager:
    AVAILABLE_ANIMAL_TYPES = {
        "bird":animal.Bird,
        "cat" :animal.Cat,
        "dog" :animal.Dog,
        "duck":animal.Duck,
        "fish":animal.Fish,
        "penguin":animal.Penguin
        }
    AVAILABLE_ABILITIES = {
        "fly" :{"msg":"空を飛んでいる"},
        "swim":{"msg":"水中を泳いでいる"},
        }
    SEARCH_MAP = {
        "ID": lambda a: [str(a.id)],
        "種類": lambda a: [(a.type_en or "").lower(), (a.type_jp or "")],  
        "名前": lambda a: [a.name.lower()],     
        "特技": lambda a: list(a.get_all_ability().keys())
        }
    ALLOWED_SORT_KEYS = {"id", "type_en", "type_jp", "name"}
    ALLOWED_ACTIONS = {"voice", "fly", "swim"}
    
    def __init__(self, data_file="data/animals.json"):
        self.data_file    = data_file
        self.id_counter   = 1
        self.naming_count = {key: 0 for key in self.AVAILABLE_ANIMAL_TYPES}
        self.animals      = {}
        self.initial_state_json = self._get_state_as_json()

    def _get_state_as_json(self):
        """現在のマネージャの状態をJSON文字列として保存可能にする"""
        animal_list = []
        for animal in self.animals.values():
            animal_list.append({
                "id": animal.id, "name": animal.name, "type_en": animal.type_en,
                "ex_ability": animal.ex_ability
            })
        return {"id_counter": self.id_counter, "naming_count": self.naming_count, "animals": animal_list}

    def is_changed(self):
        """初期状態から変更があったかどうかを判定する"""
        return self.initial_state_json != self._get_state_as_json()
    
    # --- get method ---
    
    def get_animal(self, animal_id, raise_error=True):
        animal = self.animals.get(animal_id)
        if raise_error and animal is None:
            raise AnimalNotFoundError(f"ID:{animal_id} に該当する動物は存在しません")
        return animal
    
    def get_all_animals(self):
        return sorted(self.animals.values(), key=lambda x: x.id)    

    def get_available_animal_types(self):
        return list(self.AVAILABLE_ANIMAL_TYPES.keys())

    def get_available_abilities(self):
        return list(self.AVAILABLE_ABILITIES.keys())
        
    def add_animal(self, animal_type, name):
        target = self.AVAILABLE_ANIMAL_TYPES.get(animal_type)
        if target is None:
            raise ValueError("無効な種類の動物です")
        if len(name) > 20:
            raise ValueError("名前は20文字以内で入力してください")
        elif not name:
            raise ValueError("名前を空白にはできません")
        animal_instance = target(self.id_counter, name)
        self.animals[self.id_counter] = animal_instance
        self.id_counter += 1
        return animal_instance

    def add_random_animal(self, count):
        if not isinstance(count, int):
            try:
                count = int(count)
            except (ValueError, TypeError):
                raise ValueError("追加回数は整数で指定してください")
        if count <= 0:
            raise ValueError("追加回数は1以上を指定してください")
        added_animals = []
        for _ in range(count):
            animal_type = random.choice(list(self.AVAILABLE_ANIMAL_TYPES.keys()))
            self.naming_count[animal_type] += 1
            name   = f"{animal_type}{self.naming_count[animal_type]}"
            added_animals.append(self.add_animal(animal_type, name))
        return added_animals
    

    def remove_animal(self, animal_id):
        self.get_animal(animal_id)
        return self.animals.pop(animal_id)
    

    def edit_animal_type(self, animal_id, new_type):
        target_animal = self.get_animal(animal_id)
        
        if new_type not in self.AVAILABLE_ANIMAL_TYPES:
            raise ValueError("無効な種類の動物です")

        cls = self.AVAILABLE_ANIMAL_TYPES[new_type]
        new_animal = cls(target_animal.id, target_animal.name)
        new_animal.ex_ability = target_animal.ex_ability
        self.animals[target_animal.id] = new_animal
        return new_animal
    
    def edit_animal_name(self, animal_id, new_name):
        target_animal = self.get_animal(animal_id)
        if not new_name:
            raise ValueError("名前は空白にできません")
        if len(new_name) > 20:
            raise ValueError("名前は20文字以内で入力してください")
        
        target_animal.name = new_name
        return target_animal

    def edit_animal_ability(self, animal_id, new_ability):
        target_animal = self.get_animal(animal_id)
        if new_ability not in self.AVAILABLE_ABILITIES:
            raise ValueError("無効な特技です")
            
        target_animal.ex_ability[new_ability] = dict(self.AVAILABLE_ABILITIES[new_ability])
        return target_animal

    def act_animal(self, action_name):
        """指定された行動を、可能な全ての動物に実行させる"""
        # action_name は "voice", "fly", "swim" など、直接的なメソッド名
        if not action_name:
            return []
        if action_name not in self.ALLOWED_ACTIONS:
             raise ValueError(f"無効なアクションです: {action_name}")

        # 特定の行動に必要な能力をマッピング
        ability_map = {
            "fly": "fly",
            "swim": "swim"
        }
        required_ability = ability_map.get(action_name)

        results = [] 
        for animal in self.animals.values():
            # 必要な能力を持っているか、または能力が不要な行動（voiceなど）かを確認
            if required_ability is None or animal.has_ability(required_ability):
                if hasattr(animal, action_name):
                    method = getattr(animal, action_name) 
                    result = method()
                    if result:
                        results.append(result)
        return results

    def sort_list(self, category):
        if category not in self.ALLOWED_SORT_KEYS:
            raise ValueError(f"ソートできない属性です: {category}")
        return sorted(self.animals.values(), key=lambda a: getattr(a, category)) 

    def data_reset(self):
        self.animals.clear()
        self.id_counter   = 1
        self.naming_count = {key: 0 for key in self.AVAILABLE_ANIMAL_TYPES}
        self.initial_state_json = self._get_state_as_json()

    def search_animal(self, attr, keyword):
        """キーワードと属性で動物を検索する"""
        if attr != "すべて" and attr not in self.SEARCH_MAP:
            raise ValueError(f"無効な検索属性です: {attr}")

        if not keyword:
            return sorted(self.animals.values(), key=lambda x: x.id)

        keyword = keyword.lower()
        results = []
        for animal in self.animals.values():
            if attr == "すべて":
                values = []
                for getter in self.SEARCH_MAP.values():
                    values.extend(getter(animal))
            else:
                getter = self.SEARCH_MAP.get(attr)
                values = getter(animal)
            if any(keyword in str(v).lower() for v in values):
                results.append(animal)
                
        return sorted(results, key=lambda x: x.id)

    def save_to_file(self):
        data = self._get_state_as_json()
        try:
            # ディレクトリが存在しない場合は作成する
            directory = os.path.dirname(self.data_file)
            if directory:
                os.makedirs(directory, exist_ok=True)
                
            with open(self.data_file,"w",encoding="UTF-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            # 保存が成功したら、現在の状態を新しい「未変更」状態とする
            self.initial_state_json = self._get_state_as_json()
            return True
        except IOError:
            return False

    def load_from_file(self):
        try:
            with open(self.data_file,"r",encoding="UTF-8") as f:
                data = json.load(f)
            self.id_counter   = data.get("id_counter",1)
            loaded_count      = data.get("naming_count", {})
            for key in self.naming_count:
                if key in loaded_count:
                    self.naming_count[key] = loaded_count[key]

            for item in data.get("animals",[]):
                animal_type = item["type_en"]
                cls = self.AVAILABLE_ANIMAL_TYPES.get(animal_type)
                if cls:
                    animal = cls(item["id"],item["name"])
                    animal.ex_ability = dict(item.get("ex_ability",{}))
                    self.animals[item["id"]] = animal
            # ロードが成功したら、現在の状態を新しい「未変更」状態とする
            self.initial_state_json = self._get_state_as_json()
            return True
        except (FileNotFoundError, OSError):
            return False
        except json.JSONDecodeError:
            try:
                # 拡張子を維持したままファイル名を変更
                base, ext = os.path.splitext(self.data_file)
                os.rename(self.data_file, f"{base}_broken{ext}")
            except:
                pass
            return False
