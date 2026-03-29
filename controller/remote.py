import requests
from controller.base import BaseController

class RemoteController(BaseController):
    def __init__(self, layout, manager):
        super().__init__(layout, manager)
        self.base_url = "http://127.0.0.1:8080"
        self.session = requests.Session()

    def execute_add(self, animal_type, name):
        try:
            payload = {"type": animal_type, "name": name}
            response = self.session.post(f"{self.base_url}/animals", json=payload, timeout=5)
            response.raise_for_status()       
            self.manager.load_from_file() 

        except Exception as e:
            raise Exception(f"通信エラー: {e}")

    def execute_add_random(self, count):
        try:
            payload = {"count": int(count)}
            response = self.session.post(f"{self.base_url}/animals/random", params=payload, timeout=5)
            response.raise_for_status()       
            self.manager.load_from_file()
            
        except Exception as e:
            raise Exception(f"通信エラー: {e}")

    def execute_remove(self, animal_id):
        try:
            response = self.session.delete(f"{self.base_url}/animals/{animal_id}", timeout=5)
            
            if response.status_code != 200:
                error_detail = response.json().get("detail", "不明なエラー")
                raise Exception(f"APIエラー: {error_detail}")
            
            data = response.json()
            self.manager.load_from_file() 
            return {"id": data["id"], "name": data["name"]}
        except requests.exceptions.RequestException as e:
            raise Exception(f"通信エラー: {e}")

    def execute_edit(self, animal_id, attr, new_value):
        try:
            payload = {attr: new_value}
            response = self.session.patch(f"{self.base_url}/animals/{animal_id}", json=payload, timeout=5)
            response.raise_for_status()
            self.manager.load_from_file()
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
        return choice in self.manager.ALLOWED_ACTIONS

    def save(self):
        return "APIモードは自動保存の為 この機能は制限されています"

    def data_clear(self):
        try:
            response = self.session.post(f"{self.base_url}/system/reset", timeout=5)
            response.raise_for_status()
            self.manager.load_from_file()
        except Exception as e:
            raise Exception(f"通信エラー: {e}")
    
    def has_unsaved_changes(self):
        return False
        
