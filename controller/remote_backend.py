import requests
from .dto import AnimalDTO

class RemoteBackend:
    def __init__(self, layout):
        self.layout = layout
        self.base_url = "http://127.0.0.1:8080"
        self.session = requests.Session()


    def execute_add(self, animal_type, name):
        try:
            payload = {"type": animal_type, "name": name}
            response = self.session.post(f"{self.base_url}/animals", json=payload, timeout=5)
            response.raise_for_status()       

        except Exception as e:
            raise Exception(f"通信エラー: {e}")

    def execute_add_random(self, count):
        try:
            payload = {"count": int(count)}
            response = self.session.post(f"{self.base_url}/animals/random", params=payload, timeout=5)
            response.raise_for_status()       
        except Exception as e:
            raise Exception(f"通信エラー: {e}")

    def execute_remove(self, animal_id):
        try:
            response = self.session.delete(f"{self.base_url}/animals/{animal_id}", timeout=5)
            response.raise_for_status()
            data = response.json()
            return {"id": data["id"], "name": data["name"]}
        except Exception as e:
            raise Exception(f"通信エラー: {e}")

    def execute_edit(self, animal_id, attr, new_value):
        try:
            payload = {attr: new_value}
            response = self.session.patch(f"{self.base_url}/animals/{animal_id}", json=payload, timeout=5)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"通信エラー: {e}")

    def execute_act(self, choice):
        try:
            response = self.session.get(f"{self.base_url}/animals/act/{choice}", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"通信エラー(行動実行): {e}")
    
    def is_valid_action(self, choice):
        # 将来的にAPI側から可能なアクションを取得するように拡張も可能
        ALLOWED_ACTIONS = {"voice", "fly", "swim"}
        return choice in ALLOWED_ACTIONS
    
    def execute_search(self, attribute, keyword):
        try:
            response = self.session.get(f"{self.base_url}/animals?search_attr={attribute}&keyword={keyword}", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [self._to_dto(item) for item in data]
        except Exception as e:
            raise Exception(f"通信エラー: {e}")

    def _to_dto(self, item):
        """JSON辞書をAnimalDTOに変換"""
        return AnimalDTO(
            id       = item.get("id", 0),
            name     = item.get("name", "Unknown"),
            type_en  = item.get("type_en", "unknown"),
            type_jp  = item.get("type_jp", "不明"),
            abilities= list(item.get("abilities", {}).keys())
        )

    def execute_load(self):
        return self.execute_search("すべて", "")
        
    def save(self):
        return "APIモードは自動保存の為 この機能は制限されています"

    def clear_data(self):
        try:
            response = self.session.post(f"{self.base_url}/system/reset", timeout=5)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"通信エラー: {e}")
    
    def has_unsaved_changes(self):
        return False